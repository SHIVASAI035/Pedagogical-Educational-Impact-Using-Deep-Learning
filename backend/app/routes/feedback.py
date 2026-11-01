"""Student feedback submission and privacy-preserving aggregation."""
from __future__ import annotations

from collections import Counter

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import StudentFeedback, Subject, Teacher
from ..nlp.feedback_analyzer import analyze_feedback, analyze_text
from ..services.analytics import _feedback_aggregate
from ..utils.decorators import auth_required, current_user
from ..utils.errors import ForbiddenError, ValidationError
from ..utils.validation import as_int, as_text, payload, require_fields
from ._helpers import get_or_404, require_teacher_access, teacher_of

bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")


def _target_teacher_id() -> int:
    user = current_user()
    teacher_id = request.args.get("teacher_id", type=int)
    if teacher_id is None and user.role == "teacher":
        teacher_id = teacher_of(user).id
    if teacher_id is None:
        raise ValidationError("'teacher_id' is required.")
    return teacher_id


@bp.post("")
@auth_required
def submit_feedback():
    user = current_user()
    if user.role != "student" or not user.student_profile:
        raise ForbiddenError("Only students can submit teaching feedback.")
    data = payload()
    require_fields(data, ["teacher_id", "overall_rating"])
    teacher = get_or_404(Teacher, data["teacher_id"], "Teacher")

    ratings = {}
    for field in (
        "clarity_rating",
        "interaction_rating",
        "methodology_rating",
        "practical_rating",
        "difficulty_rating",
    ):
        ratings[field] = as_int(data.get(field, data["overall_rating"]), field, minimum=1, maximum=5)
    overall = as_int(data["overall_rating"], "overall_rating", minimum=1, maximum=5)

    subject_id = data.get("subject_id")
    if subject_id is not None:
        get_or_404(Subject, subject_id, "Subject")

    comment = as_text(data.get("comments"), "comments", max_len=1000)
    analysis = analyze_feedback(comment, list(ratings.values()) + [overall])

    feedback = StudentFeedback(
        student_id=user.student_profile.id,
        teacher_id=teacher.id,
        subject_id=subject_id,
        overall_rating=overall,
        comments=comment or None,
        sentiment_label=analysis["label"],
        sentiment_score=analysis["score"],
        is_anonymous=bool(data.get("is_anonymous", True)),
        **ratings,
    )
    db.session.add(feedback)
    db.session.commit()
    return jsonify(
        {
            "message": "Feedback submitted. Thank you for helping improve teaching.",
            "feedback": feedback.to_dict(reveal_identity=True),
            "analysis": analysis,
        }
    ), 201


@bp.get("/mine")
@auth_required
def my_feedback():
    user = current_user()
    if user.role != "student" or not user.student_profile:
        raise ForbiddenError("This endpoint is for students.")
    rows = (
        StudentFeedback.query.filter_by(student_id=user.student_profile.id)
        .order_by(StudentFeedback.created_at.desc())
        .all()
    )
    return jsonify([row.to_dict(reveal_identity=True) for row in rows])


@bp.get("/summary")
@auth_required
def summary():
    user = current_user()
    if user.role == "student":
        raise ForbiddenError("Aggregated feedback is only available to teachers and administrators.")
    teacher_id = _target_teacher_id()
    teacher = get_or_404(Teacher, teacher_id, "Teacher")
    require_teacher_access(teacher)
    rows = StudentFeedback.query.filter_by(teacher_id=teacher.id).all()
    aggregate = _feedback_aggregate(rows)
    aggregate["teacher"] = {"id": teacher.id, "full_name": teacher.user.full_name}
    aggregate["privacy"] = (
        "Only aggregate statistics and anonymised comments are returned. Student "
        "identities are never exposed through this endpoint."
    )
    return jsonify(aggregate)


@bp.get("/nlp")
@auth_required
def nlp_insights():
    user = current_user()
    if user.role == "student":
        raise ForbiddenError("Feedback insights are only available to teachers and administrators.")
    teacher_id = _target_teacher_id()
    teacher = get_or_404(Teacher, teacher_id, "Teacher")
    require_teacher_access(teacher)

    rows = StudentFeedback.query.filter_by(teacher_id=teacher.id).all()
    sentiment = Counter(row.sentiment_label or "neutral" for row in rows)
    aspect_scores: dict[str, list[float]] = {}
    keywords: Counter = Counter()
    for row in rows:
        result = analyze_text(row.comments or "")
        for keyword in result["keywords"]:
            keywords[keyword] += 1
        for aspect, score in result["aspects"].items():
            aspect_scores.setdefault(aspect, []).append(score)

    total = len(rows)
    return jsonify(
        {
            "teacher_id": teacher.id,
            "total_responses": total,
            "sentiment": {
                "positive": sentiment.get("positive", 0),
                "neutral": sentiment.get("neutral", 0),
                "negative": sentiment.get("negative", 0),
            },
            "sentiment_pct": {
                label: round(sentiment.get(label, 0) / total * 100, 1) if total else 0.0
                for label in ("positive", "neutral", "negative")
            },
            "aspect_sentiment": {
                aspect: round(sum(values) / len(values), 3)
                for aspect, values in aspect_scores.items()
            },
            "top_keywords": [{"word": word, "count": count} for word, count in keywords.most_common(15)],
            "method": "lexicon+ratings-fusion-v1",
            "limitations": [
                "Lexicon-based analysis misses sarcasm, code-mixing and implicit criticism.",
                "A neutral label can mean genuinely neutral text or text with no lexicon matches.",
                "Comments are shown without student identifiers to protect privacy.",
            ],
        }
    )


@bp.get("/recent")
@auth_required
def recent_comments():
    user = current_user()
    if user.role == "student":
        raise ForbiddenError("Comments are only available to teachers and administrators.")
    teacher_id = _target_teacher_id()
    teacher = get_or_404(Teacher, teacher_id, "Teacher")
    require_teacher_access(teacher)
    rows = (
        StudentFeedback.query.filter_by(teacher_id=teacher.id)
        .order_by(StudentFeedback.created_at.desc())
        .limit(20)
        .all()
    )
    return jsonify(
        [
            {
                "comment": row.comments,
                "sentiment": row.sentiment_label,
                "subject": row.subject.name if row.subject else None,
                "date": row.created_at.date().isoformat() if row.created_at else None,
            }
            for row in rows
            if row.comments
        ]
    )
