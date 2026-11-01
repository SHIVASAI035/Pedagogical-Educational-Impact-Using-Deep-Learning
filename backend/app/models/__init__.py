"""Database models.

Importing this package registers every model with SQLAlchemy metadata.
"""
from .academic import (
    AcademicRecord,
    Assignment,
    AssignmentSubmission,
    Attendance,
    ClassRoom,
    LearningActivity,
    Subject,
)
from .analytics import Prediction, Recommendation
from .teaching import ClassroomObservation, StudentFeedback, TeachingMethod
from .user import Student, Teacher, User

__all__ = [
    "AcademicRecord",
    "Assignment",
    "AssignmentSubmission",
    "Attendance",
    "ClassRoom",
    "LearningActivity",
    "Subject",
    "Prediction",
    "Recommendation",
    "ClassroomObservation",
    "StudentFeedback",
    "TeachingMethod",
    "Student",
    "Teacher",
    "User",
]
