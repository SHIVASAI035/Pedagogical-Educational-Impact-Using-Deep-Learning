"""Teacher management endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Teacher, User
from ..services.accounts import create_user
from ..utils.decorators import auth_required, current_user, role_required
from ..utils.errors import ForbiddenError, ValidationError
from ..utils.validation import as_email, as_password, as_str, as_text, payload, require_fields
from ._helpers import get_or_404, paginated

bp = Blueprint("teachers", __name__, url_prefix="/api/teachers")


@bp.get("")
@auth_required
def list_teachers():
    query = Teacher.query
    search = (request.args.get("search") or "").strip()
    if search:
        query = query.join(Teacher.user).filter(
            db.or_(
                Teacher.employee_code.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%"),
            )
        )
    return jsonify(paginated(query.order_by(Teacher.employee_code.asc())))


@bp.post("")
@role_required("admin")
def create_teacher():
    data = payload()
    require_fields(data, ["full_name", "email", "password", "employee_code"])
    user = create_user(
        full_name=as_str(data["full_name"], "full_name", max_len=120),
        email=as_email(data["email"]),
        password=as_password(data["password"]),
        role="teacher",
        employee_code=as_str(data["employee_code"], "employee_code", max_len=40),
        department=as_text(data.get("department"), "department", max_len=120) or None,
        specialization=as_text(data.get("specialization"), "specialization", max_len=160) or None,
    )
    return jsonify(user.teacher_profile.to_dict()), 201


@bp.get("/me")
@auth_required
def my_teacher_profile():
    user = current_user()
    if not user.teacher_profile:
        raise ForbiddenError("This account has no teacher profile.")
    return jsonify(user.teacher_profile.to_dict())


@bp.get("/<int:teacher_id>")
@auth_required
def get_teacher(teacher_id: int):
    return jsonify(get_or_404(Teacher, teacher_id, "Teacher").to_dict())


@bp.put("/<int:teacher_id>")
@auth_required
def update_teacher(teacher_id: int):
    teacher = get_or_404(Teacher, teacher_id, "Teacher")
    user = current_user()
    if user.role != "admin" and teacher.user_id != user.id:
        raise ForbiddenError("You can only update your own teacher profile.")
    data = payload()
    if "full_name" in data:
        teacher.user.full_name = as_str(data["full_name"], "full_name", max_len=120)
    if "department" in data:
        teacher.department = as_text(data["department"], "department", max_len=120)
    if "specialization" in data:
        teacher.specialization = as_text(data["specialization"], "specialization", max_len=160)
    db.session.commit()
    return jsonify(teacher.to_dict())


@bp.delete("/<int:teacher_id>")
@role_required("admin")
def delete_teacher(teacher_id: int):
    teacher = get_or_404(Teacher, teacher_id, "Teacher")
    db.session.delete(teacher.user)
    db.session.commit()
    return jsonify({"message": "Teacher and linked account deleted."})
