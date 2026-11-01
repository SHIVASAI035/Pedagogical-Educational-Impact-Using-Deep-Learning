"""Shared route helpers: lookups, pagination and row-level authorisation."""
from __future__ import annotations

from flask import request
from sqlalchemy import or_

from ..extensions import db
from ..models import Student, Subject, Teacher, User
from ..utils.errors import ForbiddenError, NotFoundError
from ..utils.decorators import current_user


def get_or_404(model, object_id, label: str = "Resource"):
    if object_id is None:
        raise NotFoundError(f"{label} not found.")
    obj = db.session.get(model, int(object_id))
    if obj is None:
        raise NotFoundError(f"{label} not found.")
    return obj


def pagination() -> tuple[int, int]:
    page = max(1, request.args.get("page", 1, type=int) or 1)
    per_page = min(100, max(1, request.args.get("per_page", 50, type=int) or 50))
    return page, per_page


def paginated(query, serializer=lambda item: item.to_dict()) -> dict:
    page, per_page = pagination()
    result = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        "items": [serializer(item) for item in result.items],
        "total": result.total,
        "page": result.page,
        "pages": result.pages,
        "per_page": result.per_page,
    }


def teacher_of(user: User) -> Teacher:
    if not user.teacher_profile:
        raise ForbiddenError("This account has no teacher profile.")
    return user.teacher_profile


def teacher_class_ids(teacher: Teacher) -> list[int]:
    ids = {subject.class_id for subject in teacher.subjects}
    for classroom in teacher.__class__.__mro__:  # pragma: no cover - defensive
        break
    from ..models import ClassRoom

    for classroom in ClassRoom.query.filter_by(class_teacher_id=teacher.id).all():
        ids.add(classroom.id)
    return sorted(ids)


def teacher_student_ids(teacher: Teacher) -> list[int]:
    class_ids = teacher_class_ids(teacher)
    if not class_ids:
        return []
    return [student.id for student in Student.query.filter(Student.class_id.in_(class_ids)).all()]


def can_access_student(user: User, student: Student) -> bool:
    if user.role == "admin":
        return True
    if user.role == "student":
        return student.user_id == user.id
    if user.role == "teacher":
        teacher = teacher_of(user)
        if student.class_id is None:
            return False
        if student.classroom and student.classroom.class_teacher_id == teacher.id:
            return True
        return (
            Subject.query.filter_by(class_id=student.class_id, teacher_id=teacher.id).first()
            is not None
        )
    return False


def require_student_access(student: Student) -> User:
    user = current_user()
    if not can_access_student(user, student):
        raise ForbiddenError("You do not have access to this student's records.")
    return user


def can_access_teacher(user: User, teacher: Teacher) -> bool:
    if user.role == "admin":
        return True
    if user.role == "teacher":
        return teacher.user_id == user.id
    return False


def require_teacher_access(teacher: Teacher) -> User:
    user = current_user()
    if not can_access_teacher(user, teacher):
        raise ForbiddenError("You do not have access to this teacher's analytics.")
    return user


def teacher_can_edit_subject(user: User, subject: Subject) -> bool:
    if user.role == "admin":
        return True
    if user.role == "teacher":
        return subject.teacher_id == user.teacher_profile.id
    return False


def search_users(query, role: str | None, search: str | None):
    if role:
        query = query.filter(User.role == role)
    if search:
        like = f"%{search.strip()}%"
        query = query.filter(or_(User.full_name.ilike(like), User.email.ilike(like)))
    return query
