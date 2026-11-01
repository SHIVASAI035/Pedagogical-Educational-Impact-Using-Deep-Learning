"""Student, teacher and pedagogical-impact analytics endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify

from ..models import Student, Teacher
from ..services.analytics import (
    engagement_analysis,
    impact_analysis,
    methodology_comparison,
    student_dashboard,
    teacher_dashboard,
)
from ..utils.decorators import auth_required, current_user, role_required
from ..utils.errors import ForbiddenError
from ._helpers import get_or_404, require_student_access, require_teacher_access

bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


@bp.get("/student/me")
@auth_required
def my_student_analytics():
    user = current_user()
    if not user.student_profile:
        raise ForbiddenError("This account has no student profile.")
    return jsonify(student_dashboard(user.student_profile.id))


@bp.get("/student/<int:student_id>")
@auth_required
def student_analytics(student_id: int):
    student = get_or_404(Student, student_id, "Student")
    require_student_access(student)
    return jsonify(student_dashboard(student.id))


@bp.get("/teacher/me")
@auth_required
def my_teacher_analytics():
    user = current_user()
    if not user.teacher_profile:
        raise ForbiddenError("This account has no teacher profile.")
    return jsonify(teacher_dashboard(user.teacher_profile.id))


@bp.get("/teacher/<int:teacher_id>")
@auth_required
def teacher_analytics(teacher_id: int):
    teacher = get_or_404(Teacher, teacher_id, "Teacher")
    require_teacher_access(teacher)
    return jsonify(teacher_dashboard(teacher.id))


@bp.get("/impact")
@role_required("admin", "teacher")
def impact():
    return jsonify(impact_analysis())


@bp.get("/methodology-comparison")
@role_required("admin", "teacher")
def methodology():
    return jsonify(methodology_comparison())


@bp.get("/engagement")
@role_required("admin", "teacher")
def engagement():
    return jsonify(engagement_analysis())
