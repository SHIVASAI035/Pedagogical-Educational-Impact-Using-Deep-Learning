"""Model predictions and explainable recommendations."""
from __future__ import annotations

from datetime import datetime

from ..extensions import db


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_version = db.Column(db.String(60), nullable=False)
    predicted_score = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False, index=True)  # low|moderate|high
    features = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    student = db.relationship("Student", back_populates="predictions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": (
                self.student.user.full_name if self.student and self.student.user else None
            ),
            "model_version": self.model_version,
            "predicted_score": round(self.predicted_score, 2),
            "risk_level": self.risk_level,
            "features": self.features,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Recommendation(db.Model):
    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    audience = db.Column(db.String(20), nullable=False, index=True)  # student|teacher
    category = db.Column(db.String(60), nullable=False)
    message = db.Column(db.String(400), nullable=False)
    rationale = db.Column(db.String(600), nullable=False)
    priority = db.Column(db.String(10), nullable=False, default="medium")  # high|medium|low
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "audience": self.audience,
            "category": self.category,
            "message": self.message,
            "rationale": self.rationale,
            "priority": self.priority,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
