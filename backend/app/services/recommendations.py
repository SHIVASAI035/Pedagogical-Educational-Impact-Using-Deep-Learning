"""Explainable, supportive recommendations for students and teachers.

Every recommendation carries the evidence that triggered it (the ``rationale``
field). Rules are transparent and threshold-based on purpose: a BTech project
should be able to justify each suggestion to a teacher or student.
"""
from __future__ import annotations

from ..extensions import db
from ..models import Recommendation, Student, StudentFeedback, Teacher
from .analytics import _feedback_aggregate, _observation_summary, teacher_dashboard
from .features import student_features


def _rec(category: str, message: str, rationale: str, priority: str = "medium") -> dict:
    return {
        "category": category,
        "message": message,
        "rationale": rationale,
        "priority": priority,
    }


def student_recommendations(student_id: int) -> list[dict]:
    student = db.session.get(Student, student_id)
    if student is None:
        return []
    features = student_features(student_id)
    recommendations: list[dict] = []

    attendance = features.get("attendance_pct", 0)
    if attendance < 75:
        recommendations.append(
            _rec(
                "Attendance",
                "Aim to attend at least 90% of scheduled classes this month.",
                f"Recorded attendance is {attendance}%, below the 75% threshold "
                "commonly used for exam eligibility.",
                "high" if attendance < 65 else "medium",
            )
        )

    completion = features.get("assignment_completion", 0)
    if completion < 70:
        recommendations.append(
            _rec(
                "Assignments",
                "Clear pending assignments first, then submit in small weekly batches.",
                f"Assignment completion is {completion}%, which suggests work is "
                "accumulating and may be affecting exam preparation.",
                "high" if completion < 50 else "medium",
            )
        )

    study_hours = features.get("study_hours", 0)
    if study_hours < 2:
        recommendations.append(
            _rec(
                "Study routine",
                "Schedule two focused 45-minute study blocks on weekdays.",
                f"Logged study time averages {study_hours} hours/day, below the "
                "2-hour baseline used in this analysis.",
                "high" if study_hours < 1 else "medium",
            )
        )

    participation = features.get("class_participation", 0)
    if participation < 50:
        recommendations.append(
            _rec(
                "Participation",
                "Prepare one question or example before each class and share it.",
                f"Class participation averages {participation}% of the observed "
                "scale, limiting feedback from the teacher.",
                "medium",
            )
        )

    engagement = features.get("learning_engagement", 0)
    if engagement < 55:
        recommendations.append(
            _rec(
                "Engagement",
                "Use active recall and short self-quizzes instead of re-reading notes.",
                f"Learning engagement averages {engagement}%, indicating passive "
                "study habits in recent activity records.",
                "medium",
            )
        )

    from .features import subject_breakdown

    breakdown = subject_breakdown(student_id)
    if breakdown:
        weakest = breakdown[-1]
        if weakest["average_pct"] < 60:
            recommendations.append(
                _rec(
                    "Subject focus",
                    f"Spend two extra sessions per week on {weakest['subject_name']}.",
                    f"{weakest['subject_name']} averages {weakest['average_pct']}%, "
                    "the lowest subject average for this student.",
                    "high" if weakest["average_pct"] < 45 else "medium",
                )
            )

    if not recommendations:
        recommendations.append(
            _rec(
                "Keep momentum",
                "Maintain your current routine and try one stretch topic this month.",
                "Attendance, assignments, study time, participation and subject "
                "averages are all above the support thresholds.",
                "low",
            )
        )
    return recommendations


def teacher_recommendations(teacher_id: int) -> list[dict]:
    teacher = db.session.get(Teacher, teacher_id)
    if teacher is None:
        return []
    feedback = StudentFeedback.query.filter_by(teacher_id=teacher_id).all()
    summary = _feedback_aggregate(feedback)
    dashboard = teacher_dashboard(teacher_id)
    observations = dashboard.get("observations", {})
    averages = summary["averages"]
    recommendations: list[dict] = []

    def below(dimension: str, threshold: float) -> bool:
        value = averages.get(dimension)
        return value is not None and value < threshold

    if below("clarity_rating", 3.5):
        recommendations.append(
            _rec(
                "Explanation clarity",
                "Start each topic with a one-minute overview and end with a summary of key points.",
                f"Average clarity rating is {averages['clarity_rating']}/5 across "
                f"{summary['count']} responses, below the 3.5 review threshold.",
                "high",
            )
        )
    if below("interaction_rating", 3.5):
        recommendations.append(
            _rec(
                "Classroom interaction",
                "Add a two-minute think-pair-share or live poll to each lesson.",
                f"Average interaction rating is {averages['interaction_rating']}/5, "
                "suggesting students want more active involvement.",
                "high",
            )
        )
    if below("practical_rating", 3.5):
        recommendations.append(
            _rec(
                "Practical examples",
                "Anchor one concept per lesson in a real-world problem or demonstration.",
                f"Average practical-example rating is {averages['practical_rating']}/5.",
                "medium",
            )
        )

    observation_averages = observations.get("averages", {})
    engagement = observation_averages.get("engagement_score")
    if engagement is not None and engagement < 6:
        recommendations.append(
            _rec(
                "Engagement design",
                "Include a short collaborative activity and check for understanding every 10 minutes.",
                f"Observed classroom engagement averages {engagement}/10 across "
                f"{observations.get('count', 0)} observations.",
                "medium",
            )
        )
    material = observation_averages.get("material_usage_score")
    if material is not None and material < 6:
        recommendations.append(
            _rec(
                "Learning materials",
                "Share a one-page summary or worksheet after each major topic.",
                f"Observed material usage averages {material}/10.",
                "low",
            )
        )

    mix = dashboard.get("methodology_mix", [])
    if len(mix) < 2:
        recommendations.append(
            _rec(
                "Methodology variety",
                "Try one alternative approach (demonstration, discussion or collaborative task) this week.",
                f"Only {len(mix)} methodology type(s) are logged, so students "
                "experience a narrow range of instructional activities.",
                "medium",
            )
        )

    negative_pct = summary["sentiment"]["negative_pct"]
    if summary["count"] >= 5 and negative_pct > 30:
        recommendations.append(
            _rec(
                "Feedback review",
                "Read the anonymised comments for recurring issues and choose one to address.",
                f"{negative_pct}% of {summary['count']} comments are negative, above "
                "the 30% review threshold.",
                "high",
            )
        )

    if not recommendations:
        recommendations.append(
            _rec(
                "Maintain and share",
                "Continue the current mix of methods and share one successful activity with colleagues.",
                "Feedback and observation indicators are at or above their review thresholds.",
                "low",
            )
        )
    return recommendations


def _persist(user_id: int, audience: str, items: list[dict]) -> list[dict]:
    Recommendation.query.filter_by(user_id=user_id, audience=audience).delete()
    records = []
    for item in items:
        record = Recommendation(
            user_id=user_id,
            audience=audience,
            category=item["category"],
            message=item["message"],
            rationale=item["rationale"],
            priority=item["priority"],
        )
        db.session.add(record)
        records.append(record)
    db.session.commit()
    return [record.to_dict() for record in records]


def generate_for_student(student_id: int) -> list[dict]:
    student = db.session.get(Student, student_id)
    if student is None:
        return []
    return _persist(student.user_id, "student", student_recommendations(student_id))


def generate_for_teacher(teacher_id: int) -> list[dict]:
    teacher = db.session.get(Teacher, teacher_id)
    if teacher is None:
        return []
    return _persist(teacher.user_id, "teacher", teacher_recommendations(teacher_id))
