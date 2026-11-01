"""Student management endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import ClassRoom, Student, User
from ..services.accounts import create_user
from ..utils.decorators import auth_required, current_user, role_required
from ..utils.errors import ConflictError, ForbiddenError, ValidationError
from ..utils.validation import as_email, as_password, as_str, as_text, payload, require_fields
from ._helpers import (
    get_or_404,
    paginated,
    require_student_access,
    teacher_class_ids,
    teacher_of,
)

bp = Blueprint("students", __name__, url_prefix="/api/students")


def _visible_query(user):
    query = Student.query
    if user.role == "teacher":
        class_ids = teacher_class_ids(teacher_of(user))
        if not class_ids:
            return query.filter(db.false())
        query = query.filter(Student.class_id.in_(class_ids))
    elif user.role == "student":
        query = query.filter(Student.user_id == user.id)
    return query


@bp.get("")
@auth_required
def list_students():
    user = current_user()
    if user.role == "student":
        raise ForbiddenError("Students can only view their own profile.")
    query = _visible_query(user)
    class_id = request.args.get("class_id", type=int)
    if class_id:
        query = query.filter(Student.class_id == class_id)
    search = (request.args.get("search") or "").strip()
    if search:
        like = f"%{search}%"
        query = query.join(Student.user).filter(
            db.or_(Student.roll_number.ilike(like), User.full_name.ilike(like))
        )
    return jsonify(paginated(query.order_by(Student.roll_number.asc())))


@bp.post("")
@role_required("admin")
def create_student():
    data = payload()
    require_fields(data, ["full_name", "email", "password", "roll_number"])
    if data.get("class_id") is not None:
        get_or_404(ClassRoom, data["class_id"], "Class")
    user = create_user(
        full_name=as_str(data["full_name"], "full_name", max_len=120),
        email=as_email(data["email"]),
        password=as_password(data["password"]),
        role="student",
        roll_number=as_str(data["roll_number"], "roll_number", max_len=40),
        class_id=data.get("class_id"),
        guardian_name=as_text(data.get("guardian_name"), "guardian_name", max_len=120) or None,
    )
    return jsonify(user.student_profile.to_dict()), 201


@bp.get("/me")
@auth_required
def my_profile():
    user = current_user()
    if not user.student_profile:
        raise ForbiddenError("This account has no student profile.")
    return jsonify(user.student_profile.to_dict())


@bp.get("/<int:student_id>")
@auth_required
def get_student(student_id: int):
    student = get_or_404(Student, student_id, "Student")
    require_student_access(student)
    return jsonify(student.to_dict())


@bp.put("/<int:student_id>")
@auth_required
def update_student(student_id: int):
    student = get_or_404(Student, student_id, "Student")
    user = current_user()
    if user.role not in ("admin", "teacher"):
        raise ForbiddenError("Only administrators and teachers can update student profiles.")
    require_student_access(student)
    data = payload()

    if "full_name" in data:
        student.user.full_name = as_str(data["full_name"], "full_name", max_len=120)
    if "guardian_name" in data:
        student.guardian_name = as_text(data["guardian_name"], "guardian_name", max_len=120)
    if "class_id" in data:
        if data["class_id"] is None:
            student.class_id = None
        else:
            classroom = get_or_404(ClassRoom, data["class_id"], "Class")
            if user.role == "teacher" and classroom.id not in teacher_class_ids(teacher_of(user)):
                raise ForbiddenError("You can only move students between your own classes.")
            student.class_id = classroom.id
    if "roll_number" in data and user.role == "admin":
        roll = as_str(data["roll_number"], "roll_number", max_len=40)
        if Student.query.filter(Student.roll_number == roll, Student.id != student.id).first():
            raise ConflictError("This roll number is already in use.")
        student.roll_number = roll
    db.session.commit()
    return jsonify(student.to_dict())


@bp.delete("/<int:student_id>")
@role_required("admin")
def delete_student(student_id: int):
    student = get_or_404(Student, student_id, "Student")
    db.session.delete(student.user)
    db.session.commit()
    return jsonify({"message": "Student and linked account deleted."})
