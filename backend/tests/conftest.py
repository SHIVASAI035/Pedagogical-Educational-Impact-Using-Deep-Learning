from __future__ import annotations

import os
import sys
from datetime import date, timedelta

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import TestConfig  # noqa: E402
from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import (  # noqa: E402
    AcademicRecord,
    Attendance,
    ClassRoom,
    LearningActivity,
    Student,
    Subject,
    Teacher,
    TeachingMethod,
    User,
)
from app.services.accounts import create_user  # noqa: E402

PASSWORD = "Password123!"


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        seed_minimal()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def seeded(app):
    return {
        "admin": User.query.filter_by(email="admin@test.edu").first(),
        "teacher": User.query.filter_by(email="teacher@test.edu").first(),
        "other_teacher": User.query.filter_by(email="teacher2@test.edu").first(),
        "student": User.query.filter_by(email="student@test.edu").first(),
        "other_student": User.query.filter_by(email="student2@test.edu").first(),
        "subject": Subject.query.first(),
        "class": ClassRoom.query.first(),
    }


def seed_minimal() -> None:
    create_user(full_name="Admin", email="admin@test.edu", password=PASSWORD, role="admin")
    teacher = create_user(
        full_name="Teacher One", email="teacher@test.edu", password=PASSWORD,
        role="teacher", employee_code="E001", department="Science",
    )
    create_user(
        full_name="Teacher Two", email="teacher2@test.edu", password=PASSWORD,
        role="teacher", employee_code="E002", department="Maths",
    )
    classroom = ClassRoom(name="Grade 9", section="A", academic_year="2025-2026")
    db.session.add(classroom)
    db.session.commit()

    subject = Subject(
        name="Science", code="SCI9A", class_id=classroom.id,
        teacher_id=teacher.teacher_profile.id,
    )
    db.session.add(subject)
    db.session.commit()

    student_user = create_user(
        full_name="Student One", email="student@test.edu", password=PASSWORD,
        role="student", roll_number="R001", class_id=classroom.id,
    )
    student_user2 = create_user(
        full_name="Student Two", email="student2@test.edu", password=PASSWORD,
        role="student", roll_number="R002", class_id=classroom.id,
    )
    db.session.commit()

    for student_user_row, base in ((student_user, 72), (student_user2, 58)):
        student = student_user_row.student_profile
        db.session.add(
            AcademicRecord(
                student_id=student.id, subject_id=subject.id, exam_name="Midterm",
                marks_obtained=base, max_marks=100, exam_date=date.today() - timedelta(days=30),
            )
        )
        for offset in range(10):
            db.session.add(
                Attendance(
                    student_id=student.id, subject_id=subject.id,
                    date=date.today() - timedelta(days=offset),
                    status="absent" if offset == 3 else "present",
                )
            )
        db.session.add(
            LearningActivity(
                student_id=student.id, date=date.today() - timedelta(days=2),
                study_hours=3.0, participation_score=7.0, engagement_score=7.5,
                assignment_completion=80.0,
            )
        )
    db.session.add(
        TeachingMethod(
            teacher_id=teacher.teacher_profile.id, subject_id=subject.id,
            methodology="Demonstration", date_used=date.today() - timedelta(days=5),
        )
    )
    db.session.commit()


def token_for(client, email: str, password: str = PASSWORD) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.get_json()
    return response.get_json()["access_token"]


def auth_headers(client, email: str, password: str = PASSWORD) -> dict:
    return {"Authorization": f"Bearer {token_for(client, email, password)}"}
