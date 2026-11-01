"""Teaching sessions and classroom observations.

These are the two records that drive the teacher analytics and the impact
module, so teachers must be able to add them from the application rather than
only through the demo seeder.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import ClassRoom, ClassroomObservation, Subject, Teacher, TeachingMethod
from ..models.teaching import METHODOLOGIES
from ..utils.decorators import auth_required, current_user
from ..utils.errors import ForbiddenError, ValidationError
from ..utils.validation import (
    as_date,
    as_float,
    as_int,
    as_str,
    as_text,
    payload,
    require_fields,
)
from ._helpers import get_or_404, paginated, teacher_of

bp = Blueprint("teaching", __name__, url_prefix="/api/teaching")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _methodology(value) -> str:
    value = as_str(value, "methodology", max_len=60)
    if value not in METHODOLOGIES:
        raise ValidationError(
            "'methodology' must be one of: " + ", ".join(METHODOLOGIES) + "."
        )
    return value


def _resolve_teacher(data: dict) -> Teacher:
    """Return the teacher a record belongs to, enforcing self-only access."""
    user = current_user()
    if user.role == "teacher":
        teacher = teacher_of(user)
        requested = data.get("teacher_id")
        if requested not in (None, ""):
            if as_int(requested, "teacher_id") != teacher.id:
                raise ForbiddenError("You can only log entries for your own teaching.")
        return teacher
    if user.role != "admin":
        raise ForbiddenError("Only teachers and administrators can log teaching records.")
    require_fields(data, ["teacher_id"])
    return get_or_404(Teacher, data["teacher_id"], "Teacher")


def _resolve_subject(data: dict, teacher: Teacher, *, required: bool = False) -> Subject | None:
    subject_id = data.get("subject_id")
    if subject_id in (None, ""):
        if required:
            raise ValidationError("'subject_id' is required.")
        return None
    subject = get_or_404(Subject, subject_id, "Subject")
    if subject.teacher_id != teacher.id:
        raise ValidationError(
            "The selected subject is not assigned to this teacher, so it cannot be logged."
        )
    return subject


def _resolve_class(data: dict) -> ClassRoom | None:
    class_id = data.get("class_id")
    if class_id in (None, ""):
        return None
    return get_or_404(ClassRoom, class_id, "Class")


def _owned_or_admin(model, object_id: int, label: str):
    user = current_user()
    obj = get_or_404(model, object_id, label)
    if user.role == "admin":
        return obj
    if user.role == "teacher" and obj.teacher_id == teacher_of(user).id:
        return obj
    raise ForbiddenError(f"You can only change your own {label.lower()}.")


# ---------------------------------------------------------------------------
# Methodology taxonomy
# ---------------------------------------------------------------------------
@bp.get("/methodologies")
@auth_required
def list_methodologies():
    return jsonify(
        [
            {
                "name": name,
                "description": _METHODOLOGY_NOTES.get(name, ""),
            }
            for name in METHODOLOGIES
        ]
    )


_METHODOLOGY_NOTES = {
    "Lecture": "Teacher-led explanation with minimal student activity.",
    "Demonstration": "Teacher shows a process or worked example step by step.",
    "Collaborative Learning": "Students work in pairs or small groups on a shared task.",
    "Flipped Classroom": "Content studied before class; class time used for practice.",
    "Project Based Learning": "Sustained work producing a tangible artefact.",
    "Discussion": "Structured whole-class or small-group dialogue.",
}


# ---------------------------------------------------------------------------
# Teaching sessions
# ---------------------------------------------------------------------------
@bp.get("/sessions")
@auth_required
def list_sessions():
    user = current_user()
    query = TeachingMethod.query
    if user.role == "teacher":
        query = query.filter(TeachingMethod.teacher_id == teacher_of(user).id)
    elif user.role != "admin":
        raise ForbiddenError("Only teachers and administrators can read teaching sessions.")

    teacher_id = request.args.get("teacher_id", type=int)
    if teacher_id:
        query = query.filter(TeachingMethod.teacher_id == teacher_id)
    subject_id = request.args.get("subject_id", type=int)
    if subject_id:
        query = query.filter(TeachingMethod.subject_id == subject_id)

    query = query.order_by(TeachingMethod.date_used.desc(), TeachingMethod.id.desc())
    return jsonify(paginated(query))


@bp.post("/sessions")
@auth_required
def create_session():
    data = payload()
    teacher = _resolve_teacher(data)
    require_fields(data, ["methodology", "date_used"])
    subject = _resolve_subject(data, teacher)
    session = TeachingMethod(
        teacher_id=teacher.id,
        subject_id=subject.id if subject else None,
        methodology=_methodology(data["methodology"]),
        description=as_text(data.get("description"), "description", max_len=1000),
        date_used=as_date(data["date_used"], "date_used"),
        duration_minutes=as_int(
            data.get("duration_minutes", 45), "duration_minutes", minimum=5, maximum=600
        ),
    )
    db.session.add(session)
    db.session.commit()
    return jsonify(session.to_dict()), 201


@bp.put("/sessions/<int:session_id>")
@auth_required
def update_session(session_id: int):
    session = _owned_or_admin(TeachingMethod, session_id, "Teaching session")
    data = payload()
    if "methodology" in data:
        session.methodology = _methodology(data["methodology"])
    if "description" in data:
        session.description = as_text(data["description"], "description", max_len=1000)
    if "date_used" in data:
        session.date_used = as_date(data["date_used"], "date_used")
    if "duration_minutes" in data:
        session.duration_minutes = as_int(
            data["duration_minutes"], "duration_minutes", minimum=5, maximum=600
        )
    if "subject_id" in data:
        subject = _resolve_subject(data, session.teacher)
        session.subject_id = subject.id if subject else None
    db.session.commit()
    return jsonify(session.to_dict())


@bp.delete("/sessions/<int:session_id>")
@auth_required
def delete_session(session_id: int):
    session = _owned_or_admin(TeachingMethod, session_id, "Teaching session")
    db.session.delete(session)
    db.session.commit()
    return jsonify({"message": "Teaching session deleted."})


# ---------------------------------------------------------------------------
# Classroom observations
# ---------------------------------------------------------------------------
@bp.get("/observations")
@auth_required
def list_observations():
    user = current_user()
    query = ClassroomObservation.query
    if user.role == "teacher":
        query = query.filter(ClassroomObservation.teacher_id == teacher_of(user).id)
    elif user.role != "admin":
        raise ForbiddenError("Only teachers and administrators can read classroom observations.")

    teacher_id = request.args.get("teacher_id", type=int)
    if teacher_id:
        query = query.filter(ClassroomObservation.teacher_id == teacher_id)

    query = query.order_by(
        ClassroomObservation.observation_date.desc(), ClassroomObservation.id.desc()
    )
    return jsonify(paginated(query))


@bp.post("/observations")
@auth_required
def create_observation():
    data = payload()
    teacher = _resolve_teacher(data)
    require_fields(data, ["methodology", "observation_date"])
    subject = _resolve_subject(data, teacher)
    classroom = _resolve_class(data)
    observation = ClassroomObservation(
        teacher_id=teacher.id,
        class_id=classroom.id if classroom else (subject.class_id if subject else None),
        subject_id=subject.id if subject else None,
        methodology=_methodology(data["methodology"]),
        observation_date=as_date(data["observation_date"], "observation_date"),
        interaction_score=as_float(
            data.get("interaction_score", 0), "interaction_score", minimum=0, maximum=10
        ),
        clarity_score=as_float(
            data.get("clarity_score", 0), "clarity_score", minimum=0, maximum=10
        ),
        engagement_score=as_float(
            data.get("engagement_score", 0), "engagement_score", minimum=0, maximum=10
        ),
        practical_examples_score=as_float(
            data.get("practical_examples_score", 0),
            "practical_examples_score",
            minimum=0,
            maximum=10,
        ),
        material_usage_score=as_float(
            data.get("material_usage_score", 0), "material_usage_score", minimum=0, maximum=10
        ),
        observer_notes=as_text(data.get("observer_notes"), "observer_notes", max_len=1000),
        observer_id=current_user().id,
    )
    db.session.add(observation)
    db.session.commit()
    return jsonify(observation.to_dict()), 201


@bp.put("/observations/<int:observation_id>")
@auth_required
def update_observation(observation_id: int):
    observation = _owned_or_admin(ClassroomObservation, observation_id, "Observation")
    data = payload()
    score_fields = (
        "interaction_score",
        "clarity_score",
        "engagement_score",
        "practical_examples_score",
        "material_usage_score",
    )
    for field in score_fields:
        if field in data:
            setattr(
                observation, field, as_float(data[field], field, minimum=0, maximum=10)
            )
    if "methodology" in data:
        observation.methodology = _methodology(data["methodology"])
    if "observation_date" in data:
        observation.observation_date = as_date(data["observation_date"], "observation_date")
    if "observer_notes" in data:
        observation.observer_notes = as_text(
            data["observer_notes"], "observer_notes", max_len=1000
        )
    if "class_id" in data:
        classroom = _resolve_class(data)
        observation.class_id = classroom.id if classroom else None
    db.session.commit()
    return jsonify(observation.to_dict())


@bp.delete("/observations/<int:observation_id>")
@auth_required
def delete_observation(observation_id: int):
    observation = _owned_or_admin(ClassroomObservation, observation_id, "Observation")
    db.session.delete(observation)
    db.session.commit()
    return jsonify({"message": "Classroom observation deleted."})
