"""Printable report payloads for students, teachers and overall impact."""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify

from ..deep_learning import predictor
from ..models import Prediction, Student, StudentFeedback, Teacher
from ..services.analytics import admin_overview, impact_analysis, student_dashboard, teacher_dashboard
from ..services.recommendations import generate_for_student, generate_for_teacher
from ..utils.decorators import auth_required, role_required
from ._helpers import get_or_404, require_student_access, require_teacher_access

bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@bp.get("/student/<int:student_id>")
@auth_required
def student_report(student_id: int):
    student = get_or_404(Student, student_id, "Student")
    require_student_access(student)
    predictions = (
        Prediction.query.filter_by(student_id=student.id)
        .order_by(Prediction.created_at.desc())
        .limit(10)
        .all()
    )
    feedback_count = StudentFeedback.query.filter_by(student_id=student.id).count()
    return jsonify(
        {
            "report_type": "student_academic_report",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "student": student.to_dict(),
            "analytics": student_dashboard(student.id),
            "prediction_history": [row.to_dict() for row in predictions],
            "recommendations": generate_for_student(student.id),
            "feedback_submitted": feedback_count,
            "disclaimer": (
                "This report combines recorded data with a model trained on synthetic "
                "data. It supports, and does not replace, professional academic judgement."
            ),
        }
    )


@bp.get("/teacher/<int:teacher_id>")
@auth_required
def teacher_report(teacher_id: int):
    teacher = get_or_404(Teacher, teacher_id, "Teacher")
    require_teacher_access(teacher)
    return jsonify(
        {
            "report_type": "teacher_analytics_report",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "teacher": teacher.to_dict(),
            "analytics": teacher_dashboard(teacher.id),
            "recommendations": generate_for_teacher(teacher.id),
            "disclaimer": (
                "Indicators are contextual and based on limited observations. They are "
                "not a performance rating and should be discussed with the teacher."
            ),
        }
    )


@bp.get("/impact")
@role_required("admin")
def impact_report():
    return jsonify(
        {
            "report_type": "pedagogical_impact_report",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "overview": admin_overview(),
            "impact": impact_analysis(),
            "model": predictor.metrics() if predictor.is_ready() else {"ready": False},
            "disclaimer": (
                "Observational analysis. Differences between methodologies are "
                "associations and must not be presented as causal effects."
            ),
        }
    )
