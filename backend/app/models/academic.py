"""Academic structure and day-to-day learning records."""
from __future__ import annotations

from datetime import date, datetime

from ..extensions import db


class ClassRoom(db.Model):
    __tablename__ = "classes"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    section = db.Column(db.String(20), nullable=False, default="A")
    academic_year = db.Column(db.String(20), nullable=False)
    class_teacher_id = db.Column(
        db.Integer, db.ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    students = db.relationship("Student", back_populates="classroom")
    subjects = db.relationship(
        "Subject", back_populates="classroom",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    assignments = db.relationship("Assignment", back_populates="classroom")

    __table_args__ = (
        db.UniqueConstraint("name", "section", "academic_year", name="uq_class_section_year"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "section": self.section,
            "academic_year": self.academic_year,
            "class_teacher_id": self.class_teacher_id,
            "student_count": len(self.students),
            "subject_count": len(self.subjects),
        }


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(30), nullable=False, index=True)
    class_id = db.Column(
        db.Integer, db.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    teacher_id = db.Column(
        db.Integer, db.ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    classroom = db.relationship("ClassRoom", back_populates="subjects")
    teacher = db.relationship("Teacher", back_populates="subjects")
    records = db.relationship(
        "AcademicRecord", back_populates="subject",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    attendance = db.relationship("Attendance", back_populates="subject")
    assignments = db.relationship(
        "Assignment", back_populates="subject",
        cascade="all, delete-orphan", passive_deletes=True,
    )

    __table_args__ = (
        db.UniqueConstraint("code", "class_id", name="uq_subject_code_class"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "class_id": self.class_id,
            "class_name": self.classroom.name if self.classroom else None,
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher.user.full_name if self.teacher and self.teacher.user else None,
        }


class AcademicRecord(db.Model):
    __tablename__ = "academic_records"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    exam_name = db.Column(db.String(80), nullable=False)
    marks_obtained = db.Column(db.Float, nullable=False)
    max_marks = db.Column(db.Float, nullable=False, default=100.0)
    exam_date = db.Column(db.Date, nullable=False, default=date.today)
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="records")
    subject = db.relationship("Subject", back_populates="records")

    __table_args__ = (
        db.Index("ix_record_student_subject_date", "student_id", "subject_id", "exam_date"),
    )

    @property
    def percentage(self) -> float:
        if not self.max_marks:
            return 0.0
        return round((self.marks_obtained / self.max_marks) * 100, 2)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.user.full_name if self.student and self.student.user else None,
            "subject_id": self.subject_id,
            "subject_name": self.subject.name if self.subject else None,
            "exam_name": self.exam_name,
            "marks_obtained": self.marks_obtained,
            "max_marks": self.max_marks,
            "percentage": self.percentage,
            "exam_date": self.exam_date.isoformat() if self.exam_date else None,
        }


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    status = db.Column(db.String(12), nullable=False, default="present")  # present|absent|late
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="attendance")
    subject = db.relationship("Subject", back_populates="attendance")

    __table_args__ = (
        db.UniqueConstraint("student_id", "subject_id", "date", name="uq_attendance_student_subject_date"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.user.full_name if self.student and self.student.user else None,
            "subject_id": self.subject_id,
            "date": self.date.isoformat() if self.date else None,
            "status": self.status,
        }


class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(
        db.Integer, db.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    class_id = db.Column(
        db.Integer, db.ForeignKey("classes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=False)
    max_marks = db.Column(db.Float, nullable=False, default=20.0)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    subject = db.relationship("Subject", back_populates="assignments")
    classroom = db.relationship("ClassRoom", back_populates="assignments")
    submissions = db.relationship(
        "AssignmentSubmission", back_populates="assignment",
        cascade="all, delete-orphan", passive_deletes=True,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "subject_id": self.subject_id,
            "subject_name": self.subject.name if self.subject else None,
            "class_id": self.class_id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "max_marks": self.max_marks,
            "submission_count": len(self.submissions),
        }


class AssignmentSubmission(db.Model):
    __tablename__ = "assignment_submissions"

    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(
        db.Integer, db.ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status = db.Column(db.String(20), nullable=False, default="submitted")  # submitted|pending|late
    marks = db.Column(db.Float)
    submitted_at = db.Column(db.DateTime)

    assignment = db.relationship("Assignment", back_populates="submissions")
    student = db.relationship("Student", back_populates="submissions")

    __table_args__ = (
        db.UniqueConstraint("assignment_id", "student_id", name="uq_submission_assignment_student"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "assignment_title": self.assignment.title if self.assignment else None,
            "student_id": self.student_id,
            "status": self.status,
            "marks": self.marks,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
        }


class LearningActivity(db.Model):
    __tablename__ = "learning_activity"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    study_hours = db.Column(db.Float, nullable=False, default=0.0)
    participation_score = db.Column(db.Float, nullable=False, default=0.0)  # 0-10
    engagement_score = db.Column(db.Float, nullable=False, default=0.0)     # 0-10
    assignment_completion = db.Column(db.Float, nullable=False, default=0.0)  # 0-100
    notes = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="activities")

    __table_args__ = (
        db.UniqueConstraint("student_id", "date", name="uq_activity_student_date"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "date": self.date.isoformat() if self.date else None,
            "study_hours": self.study_hours,
            "participation_score": self.participation_score,
            "engagement_score": self.engagement_score,
            "assignment_completion": self.assignment_completion,
            "notes": self.notes,
        }
