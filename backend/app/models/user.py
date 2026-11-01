"""User, student and teacher identities."""
from __future__ import annotations

from datetime import date, datetime

from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(190), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)  # admin|teacher|student
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    student_profile = db.relationship(
        "Student", back_populates="user", uselist=False,
        cascade="all, delete-orphan", passive_deletes=True,
    )
    teacher_profile = db.relationship(
        "Teacher", back_populates="user", uselist=False,
        cascade="all, delete-orphan", passive_deletes=True,
    )

    # ---- password helpers -------------------------------------------------
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    roll_number = db.Column(db.String(40), unique=True, nullable=False, index=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classes.id"), nullable=True, index=True)
    guardian_name = db.Column(db.String(120))
    date_of_birth = db.Column(db.Date)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="student_profile")
    classroom = db.relationship("ClassRoom", back_populates="students")
    records = db.relationship(
        "AcademicRecord", back_populates="student",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    attendance = db.relationship(
        "Attendance", back_populates="student",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    submissions = db.relationship(
        "AssignmentSubmission", back_populates="student",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    activities = db.relationship(
        "LearningActivity", back_populates="student",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    feedbacks = db.relationship(
        "StudentFeedback", back_populates="student",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    predictions = db.relationship(
        "Prediction", back_populates="student",
        cascade="all, delete-orphan", passive_deletes=True,
    )

    def to_dict(self, include_user: bool = True) -> dict:
        data = {
            "id": self.id,
            "roll_number": self.roll_number,
            "class_id": self.class_id,
            "class_name": self.classroom.name if self.classroom else None,
            "guardian_name": self.guardian_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "user_id": self.user_id,
        }
        if include_user and self.user:
            data.update(
                {
                    "full_name": self.user.full_name,
                    "email": self.user.email,
                    "is_active": self.user.is_active,
                }
            )
        return data


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    employee_code = db.Column(db.String(40), unique=True, nullable=False, index=True)
    department = db.Column(db.String(120))
    specialization = db.Column(db.String(160))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="teacher_profile")
    subjects = db.relationship("Subject", back_populates="teacher")
    teaching_methods = db.relationship(
        "TeachingMethod", back_populates="teacher",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    observations = db.relationship(
        "ClassroomObservation", back_populates="teacher",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    feedbacks = db.relationship(
        "StudentFeedback", back_populates="teacher",
        cascade="all, delete-orphan", passive_deletes=True,
    )

    def to_dict(self, include_user: bool = True) -> dict:
        data = {
            "id": self.id,
            "employee_code": self.employee_code,
            "department": self.department,
            "specialization": self.specialization,
            "user_id": self.user_id,
            "subject_count": len(self.subjects),
        }
        if include_user and self.user:
            data.update(
                {
                    "full_name": self.user.full_name,
                    "email": self.user.email,
                    "is_active": self.user.is_active,
                }
            )
        return data
