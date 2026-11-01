"""Deep-learning training, prediction and evaluation endpoints."""
from __future__ import annotations

from flask import Blueprint, jsonify, request

from ..deep_learning import predictor
from ..deep_learning.train_student_ann import train as train_model
from ..extensions import db
from ..models import Prediction, Student
from ..services.features import public_features, student_features
from ..utils.decorators import auth_required, current_user, role_required
from ..utils.errors import ModelNotTrainedError, ValidationError
from ._helpers import get_or_404, require_student_access

bp = Blueprint("dl", __name__, url_prefix="/api/dl")


def _predict_and_store(student: Student) -> dict:
    features = student_features(student.id)
    if not features:
        raise ValidationError("No feature data available for this student.")
    if features.get("_completeness", 0) == 0:
        raise ValidationError(
            "This student has no attendance, marks or activity records to base a prediction on."
        )
    result = predictor.predict(public_features(features))
    result["confidence"] = features.get("_confidence")
    result["completeness"] = features.get("_completeness")

    record = Prediction(
        student_id=student.id,
        model_version=result["model_version"],
        predicted_score=result["predicted_score"],
        risk_level=result["risk_level"],
        features=public_features(features),
    )
    db.session.add(record)
    db.session.commit()
    result["prediction_id"] = record.id
    result["created_at"] = record.created_at.isoformat()
    result["student_id"] = student.id
    result["student_name"] = student.user.full_name if student.user else None
    return result


@bp.get("/status")
@auth_required
def status():
    return jsonify(
        {
            "ready": predictor.is_ready(),
            "model_version": predictor.metrics().get("model_version") if predictor.is_ready() else None,
            "features": predictor.FEATURES,
        }
    )


@bp.get("/metrics")
@auth_required
def metrics():
    if not predictor.is_ready():
        raise ModelNotTrainedError(
            "No trained model is available. An administrator can train it from the admin dashboard."
        )
    return jsonify(predictor.metrics())


@bp.post("/train")
@role_required("admin")
def train():
    metrics_payload = train_model(verbose=0)
    return jsonify(
        {
            "message": "Model trained successfully.",
            "metrics": metrics_payload["test_metrics"],
            "epochs_run": metrics_payload["training"]["epochs_run"],
            "model_version": metrics_payload["model_version"],
        }
    )


@bp.post("/predict/<int:student_id>")
@auth_required
def predict_student(student_id: int):
    student = get_or_404(Student, student_id, "Student")
    require_student_access(student)
    return jsonify(_predict_and_store(student)), 201


@bp.post("/predict/me")
@auth_required
def predict_me():
    user = current_user()
    if not user.student_profile:
        raise ValidationError("This account has no student profile.")
    return jsonify(_predict_and_store(user.student_profile)), 201


@bp.get("/predictions")
@auth_required
def prediction_history():
    user = current_user()
    student_id = request.args.get("student_id", type=int)
    query = Prediction.query
    if user.role == "student":
        query = query.filter(Prediction.student_id == user.student_profile.id)
    elif student_id:
        require_student_access(get_or_404(Student, student_id, "Student"))
        query = query.filter(Prediction.student_id == student_id)
    elif user.role == "teacher":
        from ._helpers import teacher_student_ids

        query = query.filter(Prediction.student_id.in_(teacher_student_ids(user.teacher_profile)))
    query = query.order_by(Prediction.created_at.desc()).limit(100)
    return jsonify([row.to_dict() for row in query.all()])
