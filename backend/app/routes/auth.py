"""Registration, login, profile and password endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify
from flask_jwt_extended import create_access_token, verify_jwt_in_request

from ..extensions import db
from ..services.accounts import create_user
from ..utils.decorators import auth_required, current_user
from ..utils.errors import ForbiddenError, ValidationError
from ..utils.validation import (
    as_email,
    as_password,
    as_role,
    as_str,
    as_text,
    payload,
    require_fields,
)

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _user_payload(user) -> dict:
    data = user.to_dict()
    data["student_id"] = user.student_profile.id if user.student_profile else None
    data["teacher_id"] = user.teacher_profile.id if user.teacher_profile else None
    if user.student_profile:
        data["roll_number"] = user.student_profile.roll_number
        data["class_id"] = user.student_profile.class_id
        data["class_name"] = (
            user.student_profile.classroom.name
            if user.student_profile.classroom
            else None
        )
    if user.teacher_profile:
        data["employee_code"] = user.teacher_profile.employee_code
        data["department"] = user.teacher_profile.department
    return data


def _token(user) -> str:
    return create_access_token(
        identity=str(user.id), additional_claims={"role": user.role}
    )


@bp.post("/register")
def register():
    data = payload()
    require_fields(data, ["full_name", "email", "password"])
    role = as_role(data.get("role", "student"))

    # Public self-registration is limited to students. Creating staff accounts
    # requires an authenticated administrator.
    if role != "student":
        verify_jwt_in_request()
        actor = current_user()
        if actor.role != "admin":
            raise ForbiddenError("Only administrators can create teacher or admin accounts.")

    user = create_user(
        full_name=as_str(data["full_name"], "full_name", max_len=120),
        email=as_email(data["email"]),
        password=as_password(data["password"]),
        role=role,
        roll_number=as_text(data.get("roll_number"), "roll_number", max_len=40) or None,
        class_id=data.get("class_id"),
        guardian_name=as_text(data.get("guardian_name"), "guardian_name", max_len=120) or None,
        employee_code=as_text(data.get("employee_code"), "employee_code", max_len=40) or None,
        department=as_text(data.get("department"), "department", max_len=120) or None,
        specialization=as_text(data.get("specialization"), "specialization", max_len=160) or None,
    )
    return jsonify({"access_token": _token(user), "user": _user_payload(user)}), 201


@bp.post("/login")
def login():
    data = payload()
    require_fields(data, ["email", "password"])
    email = as_email(data["email"])
    from ..models import User

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(data["password"]):
        raise ValidationError("Invalid email or password.")
    if not user.is_active:
        raise ForbiddenError("This account has been deactivated. Contact an administrator.")
    return jsonify({"access_token": _token(user), "user": _user_payload(user)})


@bp.get("/profile")
@auth_required
def profile():
    return jsonify(_user_payload(current_user()))


@bp.put("/profile")
@auth_required
def update_profile():
    user = current_user()
    data = payload()
    if "full_name" in data:
        user.full_name = as_str(data["full_name"], "full_name", max_len=120)
    if user.student_profile and "guardian_name" in data:
        user.student_profile.guardian_name = as_text(
            data["guardian_name"], "guardian_name", max_len=120
        )
    if user.teacher_profile:
        if "department" in data:
            user.teacher_profile.department = as_text(data["department"], "department", 120)
        if "specialization" in data:
            user.teacher_profile.specialization = as_text(
                data["specialization"], "specialization", 160
            )
    db.session.commit()
    return jsonify(_user_payload(user))


@bp.post("/change-password")
@auth_required
def change_password():
    user = current_user()
    data = payload()
    require_fields(data, ["current_password", "new_password"])
    if not user.check_password(data["current_password"]):
        raise ValidationError("The current password is incorrect.")
    user.set_password(as_password(data["new_password"]))
    db.session.commit()
    return jsonify({"message": "Password updated successfully."})
