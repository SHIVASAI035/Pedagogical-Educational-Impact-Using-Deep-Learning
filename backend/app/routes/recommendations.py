"""Explainable recommendation endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import Recommendation, Student, Teacher
from ..services.recommendations import (
    generate_for_student,
    generate_for_teacher,
    student_recommendations,
    teacher_recommendations,
)
from ..utils.decorators import auth_required, current_user, role_required
from ..utils.errors import ForbiddenError, ValidationError
from ..utils.validation import payload
from ._helpers import get_or_404, require_student_access, require_teacher_access

bp = Blueprint("recommendations", __name__, url_prefix="/api/recommendations")


@bp.get("/me")
@auth_required
def my_recommendations():
    user = current_user()
    if user.student_profile:
        return jsonify(generate_for_student(user.student_profile.id))
    if user.teacher_profile:
        return jsonify(generate_for_teacher(user.teacher_profile.id))
    return jsonify([])


@bp.get("/student/<int:student_id>")
@auth_required
def student_recommendation_list(student_id: int):
    student = get_or_404(Student, student_id, "Student")
    require_student_access(student)
    return jsonify(generate_for_student(student.id))


@bp.get("/teacher/<int:teacher_id>")
@auth_required
def teacher_recommendation_list(teacher_id: int):
    teacher = get_or_404(Teacher, teacher_id, "Teacher")
    require_teacher_access(teacher)
    return jsonify(generate_for_teacher(teacher.id))


@bp.post("/generate")
@auth_required
def generate():
    user = current_user()
    data = payload()
    if data.get("student_id") is not None:
        if user.role not in ("admin", "teacher"):
            raise ForbiddenError("Only teachers and administrators can generate student recommendations.")
        student = get_or_404(Student, data["student_id"], "Student")
        require_student_access(student)
        return jsonify(generate_for_student(student.id)), 201
    if data.get("teacher_id") is not None:
        teacher = get_or_404(Teacher, data["teacher_id"], "Teacher")
        require_teacher_access(teacher)
        return jsonify(generate_for_teacher(teacher.id)), 201
    if user.student_profile:
        return jsonify(generate_for_student(user.student_profile.id)), 201
    if user.teacher_profile:
        return jsonify(generate_for_teacher(user.teacher_profile.id)), 201
    raise ValidationError("Provide 'student_id' or 'teacher_id'.")


@bp.get("/preview/student/<int:student_id>")
@role_required("admin", "teacher")
def preview_student(student_id: int):
    student = get_or_404(Student, student_id, "Student")
    require_student_access(student)
    return jsonify(student_recommendations(student.id))


@bp.get("/preview/teacher/<int:teacher_id>")
@role_required("admin", "teacher")
def preview_teacher(teacher_id: int):
    teacher = get_or_404(Teacher, teacher_id, "Teacher")
    require_teacher_access(teacher)
    return jsonify(teacher_recommendations(teacher.id))
