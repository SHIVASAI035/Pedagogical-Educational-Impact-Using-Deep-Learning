"""End-to-end API tests (SQLite in-memory; MySQL is verified separately)."""
from __future__ import annotations

from datetime import date, timedelta

from app.extensions import db
from app.models import AcademicRecord, Attendance, Student, StudentFeedback, Subject
from app.nlp.feedback_analyzer import analyze_feedback, analyze_text

from .conftest import PASSWORD, auth_headers, token_for


# ---------------------------------------------------------------------------
# 1-4: authentication and role-based access
# ---------------------------------------------------------------------------
def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_admin_login(client):
    response = client.post(
        "/api/auth/login", json={"email": "admin@test.edu", "password": PASSWORD}
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["user"]["role"] == "admin"
    assert body["access_token"]


def test_teacher_and_student_login(client):
    teacher = client.post(
        "/api/auth/login", json={"email": "teacher@test.edu", "password": PASSWORD}
    )
    student = client.post(
        "/api/auth/login", json={"email": "student@test.edu", "password": PASSWORD}
    )
    assert teacher.status_code == 200 and teacher.get_json()["user"]["role"] == "teacher"
    assert student.status_code == 200 and student.get_json()["user"]["role"] == "student"
    assert student.get_json()["user"]["student_id"]


def test_invalid_login(client):
    response = client.post(
        "/api/auth/login", json={"email": "student@test.edu", "password": "wrong-password"}
    )
    assert response.status_code == 422


def test_role_based_permissions(client, seeded):
    student_headers = auth_headers(client, "student@test.edu")
    teacher_headers = auth_headers(client, "teacher@test.edu")
    admin_headers = auth_headers(client, "admin@test.edu")

    assert client.get("/api/admin/stats", headers=student_headers).status_code == 403
    assert client.get("/api/admin/stats", headers=teacher_headers).status_code == 403
    assert client.get("/api/admin/stats", headers=admin_headers).status_code == 200
    assert client.get("/api/admin/stats").status_code == 401


def test_student_cannot_read_other_student(client, seeded):
    headers = auth_headers(client, "student@test.edu")
    other = seeded["other_student"].student_profile
    own = seeded["student"].student_profile
    assert client.get(f"/api/analytics/student/{other.id}", headers=headers).status_code == 403
    assert client.get(f"/api/analytics/student/{own.id}", headers=headers).status_code == 200
    assert client.get("/api/analytics/student/me", headers=headers).status_code == 200


# ---------------------------------------------------------------------------
# 5-7: records management
# ---------------------------------------------------------------------------
def test_admin_creates_student_and_teacher(client, seeded):
    admin = auth_headers(client, "admin@test.edu")
    response = client.post(
        "/api/students",
        headers=admin,
        json={
            "full_name": "New Student",
            "email": "newstudent@test.edu",
            "password": PASSWORD,
            "roll_number": "R099",
            "class_id": seeded["class"].id,
        },
    )
    assert response.status_code == 201
    assert response.get_json()["roll_number"] == "R099"

    duplicate = client.post(
        "/api/students",
        headers=admin,
        json={
            "full_name": "Duplicate",
            "email": "newstudent@test.edu",
            "password": PASSWORD,
            "roll_number": "R100",
        },
    )
    assert duplicate.status_code == 409

    teacher = client.post(
        "/api/teachers",
        headers=admin,
        json={
            "full_name": "New Teacher",
            "email": "newteacher@test.edu",
            "password": PASSWORD,
            "employee_code": "E099",
            "department": "Arts",
        },
    )
    assert teacher.status_code == 201


def test_teacher_enters_marks_only_for_own_subject(client, seeded):
    headers = auth_headers(client, "teacher@test.edu")
    student = seeded["student"].student_profile
    subject = seeded["subject"]
    response = client.post(
        "/api/academics/records",
        headers=headers,
        json={
            "student_id": student.id,
            "subject_id": subject.id,
            "exam_name": "Unit Test",
            "marks_obtained": 81,
            "max_marks": 100,
            "exam_date": date.today().isoformat(),
        },
    )
    assert response.status_code == 201
    assert response.get_json()["percentage"] == 81.0

    other_headers = auth_headers(client, "teacher2@test.edu")
    forbidden = client.post(
        "/api/academics/records",
        headers=other_headers,
        json={
            "student_id": student.id,
            "subject_id": subject.id,
            "exam_name": "Unit Test",
            "marks_obtained": 60,
        },
    )
    assert forbidden.status_code == 403

    student_headers = auth_headers(client, "student@test.edu")
    assert client.post(
        "/api/academics/records",
        headers=student_headers,
        json={"student_id": student.id, "subject_id": subject.id,
              "exam_name": "X", "marks_obtained": 99},
    ).status_code == 403


def test_attendance_bulk_and_marks_validation(client, seeded):
    headers = auth_headers(client, "teacher@test.edu")
    student = seeded["student"].student_profile
    subject = seeded["subject"]
    response = client.post(
        "/api/academics/attendance",
        headers=headers,
        json={
            "records": [
                {"student_id": student.id, "subject_id": subject.id,
                 "date": date.today().isoformat(), "status": "present"},
                {"student_id": seeded["other_student"].student_profile.id,
                 "subject_id": subject.id, "date": date.today().isoformat(), "status": "absent"},
            ]
        },
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["created"] + payload["updated"] == 2

    invalid = client.post(
        "/api/academics/records",
        headers=headers,
        json={"student_id": student.id, "subject_id": subject.id,
              "exam_name": "Bad", "marks_obtained": 120, "max_marks": 100},
    )
    assert invalid.status_code == 422


def test_assignments_and_submission_flow(client, seeded):
    teacher = auth_headers(client, "teacher@test.edu")
    student = auth_headers(client, "student@test.edu")
    subject = seeded["subject"]
    created = client.post(
        "/api/academics/assignments",
        headers=teacher,
        json={"subject_id": subject.id, "title": "Worksheet 1",
              "due_date": (date.today() + timedelta(days=3)).isoformat(), "max_marks": 20},
    )
    assert created.status_code == 201
    assignment_id = created.get_json()["id"]

    submitted = client.post(
        "/api/academics/submissions", headers=student, json={"assignment_id": assignment_id}
    )
    assert submitted.status_code == 201
    assert submitted.get_json()["status"] == "submitted"

    listed = client.get("/api/academics/assignments", headers=student)
    assert listed.status_code == 200
    assert listed.get_json()["total"] == 1


# ---------------------------------------------------------------------------
# 8-10: deep learning
# ---------------------------------------------------------------------------
def test_ann_training_metrics_are_real(app, tmp_path, monkeypatch):
    from app.deep_learning import predictor
    from app.deep_learning.train_student_ann import train

    metrics = train(epochs=3, verbose=0, artifact_dir=str(tmp_path))
    for key in ("mae", "mse", "rmse"):
        assert isinstance(metrics["test_metrics"][key], float)
        assert metrics["test_metrics"][key] >= 0
    # R-squared can legitimately be negative for an under-trained smoke-test model.
    assert isinstance(metrics["test_metrics"]["r2"], float)
    assert metrics["test_metrics"]["r2"] <= 1.0
    assert metrics["dataset"]["synthetic"] is True
    assert metrics["dataset"]["rows_train"] > 0
    assert (tmp_path / "student_ann.keras").exists()

    monkeypatch.setattr(predictor, "ARTIFACT_DIR", str(tmp_path))
    predictor.reset_cache()
    result = predictor.predict(
        {
            "attendance_pct": 85,
            "study_hours": 3,
            "previous_marks": 70,
            "assignment_completion": 80,
            "class_participation": 65,
            "learning_engagement": 70,
            "subject_performance": 72,
        }
    )
    assert 0 <= result["predicted_score"] <= 100
    assert result["risk_level"] in {"low", "moderate", "high"}


def test_prediction_endpoint(client, seeded, tmp_path, monkeypatch):
    from app.deep_learning import predictor
    from app.deep_learning.train_student_ann import train

    train(epochs=2, verbose=0, artifact_dir=str(tmp_path))
    monkeypatch.setattr(predictor, "ARTIFACT_DIR", str(tmp_path))
    predictor.reset_cache()

    headers = auth_headers(client, "teacher@test.edu")
    student = seeded["student"].student_profile
    response = client.post(f"/api/dl/predict/{student.id}", headers=headers)
    assert response.status_code == 201
    body = response.get_json()
    assert 0 <= body["predicted_score"] <= 100
    assert body["prediction_id"]

    history = client.get(f"/api/dl/predictions?student_id={student.id}", headers=headers)
    assert history.status_code == 200
    assert len(history.get_json()) >= 1

    metrics = client.get("/api/dl/metrics", headers=headers)
    assert metrics.status_code == 200
    assert "test_metrics" in metrics.get_json()


# ---------------------------------------------------------------------------
# 11-13: feedback, NLP and impact
# ---------------------------------------------------------------------------
def test_nlp_analyzer_labels_and_aspects():
    positive = analyze_text("Very clear explanations with useful practical examples. Great class!")
    negative = analyze_text("Confusing lecture, too fast and no practical examples.")
    assert positive["label"] == "positive"
    assert negative["label"] == "negative"
    assert "clarity" in positive["aspects"]

    fused = analyze_feedback("The class was okay.", [3, 3, 3, 3, 3, 3])
    assert fused["label"] in {"neutral", "positive", "negative"}


def test_student_feedback_submission_and_privacy(client, seeded):
    student = auth_headers(client, "student@test.edu")
    teacher = auth_headers(client, "teacher@test.edu")
    teacher_id = seeded["teacher"].teacher_profile.id

    response = client.post(
        "/api/feedback",
        headers=student,
        json={
            "teacher_id": teacher_id,
            "subject_id": seeded["subject"].id,
            "clarity_rating": 5,
            "interaction_rating": 4,
            "methodology_rating": 5,
            "practical_rating": 4,
            "difficulty_rating": 3,
            "overall_rating": 5,
            "comments": "Very clear explanations and useful practical examples.",
        },
    )
    assert response.status_code == 201
    assert response.get_json()["analysis"]["label"] == "positive"

    summary = client.get(f"/api/feedback/summary?teacher_id={teacher_id}", headers=teacher)
    assert summary.status_code == 200
    assert "Student One" not in summary.get_data(as_text=True)
    assert summary.get_json()["count"] == 1

    # A different teacher cannot read this teacher's feedback summary.
    other = auth_headers(client, "teacher2@test.edu")
    assert client.get(
        f"/api/feedback/summary?teacher_id={teacher_id}", headers=other
    ).status_code == 403

    # Students cannot read aggregated feedback at all.
    assert client.get(
        f"/api/feedback/summary?teacher_id={teacher_id}", headers=student
    ).status_code == 403


def test_impact_analysis_and_methodology_comparison(client, seeded):
    headers = auth_headers(client, "admin@test.edu")
    impact = client.get("/api/analytics/impact", headers=headers)
    assert impact.status_code == 200
    body = impact.get_json()
    assert "causality_statement" in body
    assert "correlations" in body and len(body["correlations"]) >= 1
    assert body["methodology_comparison"]["methodologies"]

    comparison = client.get("/api/analytics/methodology-comparison", headers=headers)
    assert comparison.status_code == 200
    assert "anova" in comparison.get_json()


def test_teacher_analytics_and_reports(client, seeded):
    teacher = auth_headers(client, "teacher@test.edu")
    teacher_id = seeded["teacher"].teacher_profile.id
    analytics = client.get("/api/analytics/teacher/me", headers=teacher)
    assert analytics.status_code == 200
    assert "indicators" in analytics.get_json()
    assert "data_sufficiency" in analytics.get_json()

    report = client.get(f"/api/reports/teacher/{teacher_id}", headers=teacher)
    assert report.status_code == 200
    assert report.get_json()["report_type"] == "teacher_analytics_report"

    admin = auth_headers(client, "admin@test.edu")
    assert client.get("/api/reports/impact", headers=admin).status_code == 200
    assert client.get("/api/reports/impact", headers=teacher).status_code == 403


# ---------------------------------------------------------------------------
# 14: recommendations
# ---------------------------------------------------------------------------
def test_recommendations_are_explainable(client, seeded):
    headers = auth_headers(client, "student@test.edu")
    response = client.get("/api/recommendations/me", headers=headers)
    assert response.status_code == 200
    items = response.get_json()
    assert items
    assert all(item["rationale"] for item in items)

    teacher = auth_headers(client, "teacher@test.edu")
    teacher_recs = client.get("/api/recommendations/me", headers=teacher)
    assert teacher_recs.status_code == 200
    assert all(item["rationale"] for item in teacher_recs.get_json())


# ---------------------------------------------------------------------------
# extra: student dashboard and own-data isolation
# ---------------------------------------------------------------------------
def test_student_dashboard_returns_own_data(client, seeded):
    headers = auth_headers(client, "student@test.edu")
    response = client.get("/api/analytics/student/me", headers=headers)
    assert response.status_code == 200
    body = response.get_json()
    assert body["student"]["roll_number"] == "R001"
    assert body["attendance"]["records"] == 10
    assert body["academics"]["subjects"]


# ---------------------------------------------------------------------------
# 17-18: teaching sessions and classroom observations
# ---------------------------------------------------------------------------
def test_teacher_logs_session_and_observation(client, seeded):
    headers = auth_headers(client, "teacher@test.edu")
    subject = seeded["subject"]

    methodology_list = client.get("/api/teaching/methodologies", headers=headers)
    assert methodology_list.status_code == 200
    names = [item["name"] for item in methodology_list.get_json()]
    assert "Discussion" in names

    session = client.post(
        "/api/teaching/sessions",
        headers=headers,
        json={
            "subject_id": subject.id,
            "methodology": "Discussion",
            "date_used": date.today().isoformat(),
            "duration_minutes": 50,
            "description": "Structured debate on renewable energy.",
        },
    )
    assert session.status_code == 201, session.get_json()
    session_body = session.get_json()
    assert session_body["methodology"] == "Discussion"
    assert session_body["subject_name"] == subject.name

    observation = client.post(
        "/api/teaching/observations",
        headers=headers,
        json={
            "subject_id": subject.id,
            "methodology": "Discussion",
            "observation_date": date.today().isoformat(),
            "interaction_score": 8,
            "clarity_score": 7.5,
            "engagement_score": 8,
            "practical_examples_score": 7,
            "material_usage_score": 6,
            "observer_notes": "Strong questioning; more wait time needed.",
        },
    )
    assert observation.status_code == 201, observation.get_json()
    assert observation.get_json()["class_id"] == seeded["class"].id

    analytics = client.get("/api/analytics/teacher/me", headers=headers)
    assert analytics.status_code == 200
    body = analytics.get_json()
    assert body["observations"]["count"] >= 1
    assert any(item["methodology"] == "Discussion" for item in body["methodology_mix"])

    # The observation feeds the same table the analytics read from.
    listed = client.get("/api/teaching/observations", headers=headers)
    assert listed.status_code == 200
    assert listed.get_json()["total"] == 1


def test_teaching_records_respect_ownership(client, seeded):
    teacher_headers = auth_headers(client, "teacher@test.edu")
    other_teacher = seeded["other_teacher"].teacher_profile

    # A teacher may not log a session on behalf of another teacher.
    impostor = client.post(
        "/api/teaching/sessions",
        headers=teacher_headers,
        json={
            "teacher_id": other_teacher.id,
            "methodology": "Lecture",
            "date_used": date.today().isoformat(),
        },
    )
    assert impostor.status_code == 403

    # A teacher may not log against a subject they do not teach.
    admin_headers = auth_headers(client, "admin@test.edu")
    foreign_subject = client.post(
        "/api/subjects",
        headers=admin_headers,
        json={
            "name": "Mathematics",
            "code": "MAT9A",
            "class_id": seeded["class"].id,
            "teacher_id": other_teacher.id,
        },
    )
    assert foreign_subject.status_code == 201, foreign_subject.get_json()
    foreign_id = foreign_subject.get_json()["id"]

    wrong_subject = client.post(
        "/api/teaching/sessions",
        headers=teacher_headers,
        json={
            "subject_id": foreign_id,
            "methodology": "Lecture",
            "date_used": date.today().isoformat(),
        },
    )
    assert wrong_subject.status_code == 422

    # Unknown methodologies are rejected rather than silently stored.
    bad_methodology = client.post(
        "/api/teaching/sessions",
        headers=teacher_headers,
        json={"methodology": "Magic", "date_used": date.today().isoformat()},
    )
    assert bad_methodology.status_code == 422

    # Students cannot read or write teaching records.
    student_headers = auth_headers(client, "student@test.edu")
    assert client.get("/api/teaching/sessions", headers=student_headers).status_code == 403
    assert client.get("/api/teaching/observations", headers=student_headers).status_code == 403
    assert (
        client.post(
            "/api/teaching/sessions",
            headers=student_headers,
            json={"methodology": "Lecture", "date_used": date.today().isoformat()},
        ).status_code
        == 403
    )

    # Admins can read any teacher's sessions.
    admin_view = client.get(
        f"/api/teaching/sessions?teacher_id={seeded['teacher'].teacher_profile.id}",
        headers=admin_headers,
    )
    assert admin_view.status_code == 200
    assert admin_view.get_json()["total"] >= 1
