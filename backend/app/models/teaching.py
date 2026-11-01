"""Teaching methodology, classroom observation and student feedback."""
from __future__ import annotations

from datetime import date, datetime

from ..extensions import db

METHODOLOGIES = (
    "Lecture",
    "Demonstration",
    "Collaborative Learning",
    "Flipped Classroom",
    "Project Based Learning",
    "Discussion",
)


class TeachingMethod(db.Model):
    __tablename__ = "teaching_methods"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(
        db.Integer, db.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    methodology = db.Column(db.String(60), nullable=False, index=True)
    description = db.Column(db.Text)
    date_used = db.Column(db.Date, nullable=False, default=date.today, index=True)
    duration_minutes = db.Column(db.Integer, nullable=False, default=45)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    teacher = db.relationship("Teacher", back_populates="teaching_methods")
    subject = db.relationship("Subject")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher.user.full_name if self.teacher and self.teacher.user else None,
            "subject_id": self.subject_id,
            "subject_name": self.subject.name if self.subject else None,
            "methodology": self.methodology,
            "description": self.description,
            "date_used": self.date_used.isoformat() if self.date_used else None,
            "duration_minutes": self.duration_minutes,
        }


class ClassroomObservation(db.Model):
    __tablename__ = "classroom_observations"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(
        db.Integer, db.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    class_id = db.Column(
        db.Integer, db.ForeignKey("classes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    methodology = db.Column(db.String(60), nullable=False, index=True)
    observation_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    interaction_score = db.Column(db.Float, nullable=False, default=0.0)        # 0-10
    clarity_score = db.Column(db.Float, nullable=False, default=0.0)            # 0-10
    engagement_score = db.Column(db.Float, nullable=False, default=0.0)         # 0-10
    practical_examples_score = db.Column(db.Float, nullable=False, default=0.0) # 0-10
    material_usage_score = db.Column(db.Float, nullable=False, default=0.0)     # 0-10
    observer_notes = db.Column(db.Text)
    observer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    teacher = db.relationship("Teacher", back_populates="observations")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher.user.full_name if self.teacher and self.teacher.user else None,
            "class_id": self.class_id,
            "subject_id": self.subject_id,
            "methodology": self.methodology,
            "observation_date": self.observation_date.isoformat() if self.observation_date else None,
            "interaction_score": self.interaction_score,
            "clarity_score": self.clarity_score,
            "engagement_score": self.engagement_score,
            "practical_examples_score": self.practical_examples_score,
            "material_usage_score": self.material_usage_score,
            "observer_notes": self.observer_notes,
        }


class StudentFeedback(db.Model):
    __tablename__ = "student_feedback"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    teacher_id = db.Column(
        db.Integer, db.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    clarity_rating = db.Column(db.Integer, nullable=False)        # 1-5
    interaction_rating = db.Column(db.Integer, nullable=False)    # 1-5
    methodology_rating = db.Column(db.Integer, nullable=False)    # 1-5
    practical_rating = db.Column(db.Integer, nullable=False)      # 1-5
    difficulty_rating = db.Column(db.Integer, nullable=False)     # 1-5
    overall_rating = db.Column(db.Integer, nullable=False)        # 1-5
    comments = db.Column(db.Text)
    sentiment_label = db.Column(db.String(12), index=True)        # positive|neutral|negative
    sentiment_score = db.Column(db.Float)                         # -1 .. 1
    is_anonymous = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    student = db.relationship("Student", back_populates="feedbacks")
    teacher = db.relationship("Teacher", back_populates="feedbacks")
    subject = db.relationship("Subject")

    def to_dict(self, reveal_identity: bool = False) -> dict:
        data = {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "subject_id": self.subject_id,
            "subject_name": self.subject.name if self.subject else None,
            "clarity_rating": self.clarity_rating,
            "interaction_rating": self.interaction_rating,
            "methodology_rating": self.methodology_rating,
            "practical_rating": self.practical_rating,
            "difficulty_rating": self.difficulty_rating,
            "overall_rating": self.overall_rating,
            "comments": self.comments,
            "sentiment_label": self.sentiment_label,
            "sentiment_score": self.sentiment_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if reveal_identity:
            data["student_id"] = self.student_id
            data["student_name"] = (
                self.student.user.full_name if self.student and self.student.user else None
            )
        return data
