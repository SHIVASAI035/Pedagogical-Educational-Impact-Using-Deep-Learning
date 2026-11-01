"""Turn raw database records into the seven ANN input features."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import func

from ..extensions import db
from ..models import (
    AcademicRecord,
    Assignment,
    AssignmentSubmission,
    Attendance,
    LearningActivity,
    Student,
)


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def student_features(student_id: int) -> dict:
    """Compute features with the same semantics used during training.

    Each feature is on a 0-100 scale (study_hours is hours/day, 0-9).
    """
    student = db.session.get(Student, student_id)
    if student is None:
        return {}

    # --- attendance (all recorded sessions) --------------------------------
    attendance_rows = Attendance.query.filter_by(student_id=student_id).all()
    present = sum(1 for row in attendance_rows if row.status in ("present", "late"))
    attendance_pct = (
        round(present / len(attendance_rows) * 100, 2) if attendance_rows else 0.0
    )

    # --- recent learning activity (last 30 entries) ------------------------
    activities = (
        LearningActivity.query.filter_by(student_id=student_id)
        .order_by(LearningActivity.date.desc())
        .limit(30)
        .all()
    )
    study_hours = _mean([row.study_hours for row in activities])
    participation = _mean([row.participation_score * 10 for row in activities])
    engagement = _mean([row.engagement_score * 10 for row in activities])

    # --- assignment completion --------------------------------------------
    activity_completion = _mean([row.assignment_completion for row in activities])
    submission_rows = (
        db.session.query(AssignmentSubmission, Assignment)
        .join(Assignment, AssignmentSubmission.assignment_id == Assignment.id)
        .filter(AssignmentSubmission.student_id == student_id)
        .all()
    )
    if submission_rows:
        done = sum(
            1
            for submission, _ in submission_rows
            if submission.status in ("submitted", "late")
        )
        submission_completion = round(done / len(submission_rows) * 100, 2)
    else:
        submission_completion = 0.0
    assignment_completion = (
        activity_completion if activities else submission_completion
    )

    # --- marks: latest exam per subject + overall subject performance ------
    records = AcademicRecord.query.filter_by(student_id=student_id).all()
    latest: dict[int, AcademicRecord] = {}
    for record in records:
        current = latest.get(record.subject_id)
        if current is None or record.exam_date >= current.exam_date:
            latest[record.subject_id] = record

    latest_percentages = [record.percentage for record in latest.values()]
    all_percentages = [record.percentage for record in records]
    previous_marks = _mean(latest_percentages)
    subject_performance = _mean(all_percentages)

    features = {
        "attendance_pct": attendance_pct,
        "study_hours": min(9.0, study_hours),
        "previous_marks": previous_marks,
        "assignment_completion": min(100.0, assignment_completion),
        "class_participation": min(100.0, participation),
        "learning_engagement": min(100.0, engagement),
        "subject_performance": subject_performance,
    }

    # How many of the seven features are backed by real observations?
    evidence = {
        "attendance_pct": bool(attendance_rows),
        "study_hours": bool(activities),
        "previous_marks": bool(records),
        "assignment_completion": bool(activities or submission_rows),
        "class_participation": bool(activities),
        "learning_engagement": bool(activities),
        "subject_performance": bool(records),
    }
    filled = sum(evidence.values())
    features["_evidence"] = evidence
    features["_completeness"] = round(filled / len(evidence), 2)
    features["_confidence"] = (
        "high" if filled >= 6 else "medium" if filled >= 4 else "low"
    )
    return features


def public_features(features: dict) -> dict:
    """Strip internal metadata keys before storing/serialising features."""
    return {key: value for key, value in features.items() if not key.startswith("_")}


def attendance_series(student_id: int, months: int = 6) -> list[dict]:
    """Monthly attendance percentage for progress charts."""
    since = date.today() - timedelta(days=31 * months)
    rows = (
        Attendance.query.filter(
            Attendance.student_id == student_id, Attendance.date >= since
        )
        .order_by(Attendance.date.asc())
        .all()
    )
    buckets: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        buckets[row.date.strftime("%Y-%m")].append(1 if row.status != "absent" else 0)
    return [
        {"period": period, "attendance_pct": round(sum(values) / len(values) * 100, 1)}
        for period, values in sorted(buckets.items())
    ]


def marks_trend(student_id: int) -> list[dict]:
    """Average percentage per exam date, used for the progress line chart."""
    rows = (
        AcademicRecord.query.filter_by(student_id=student_id)
        .order_by(AcademicRecord.exam_date.asc())
        .all()
    )
    buckets: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        buckets[row.exam_date.isoformat()].append(row.percentage)
    return [
        {"period": period, "score": round(sum(values) / len(values), 1)}
        for period, values in sorted(buckets.items())
    ]


def subject_breakdown(student_id: int) -> list[dict]:
    rows = (
        db.session.query(
            AcademicRecord.subject_id,
            func.avg(AcademicRecord.marks_obtained * 100.0 / AcademicRecord.max_marks),
        )
        .filter(AcademicRecord.student_id == student_id)
        .group_by(AcademicRecord.subject_id)
        .all()
    )
    from ..models import Subject

    result = []
    for subject_id, average in rows:
        subject = db.session.get(Subject, subject_id)
        result.append(
            {
                "subject_id": subject_id,
                "subject_name": subject.name if subject else f"Subject {subject_id}",
                "average_pct": round(float(average or 0), 1),
            }
        )
    return sorted(result, key=lambda item: item["average_pct"], reverse=True)
