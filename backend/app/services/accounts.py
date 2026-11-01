"""Account creation/update shared by auth, admin and management routes."""
from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import Student, Teacher, User
from ..utils.errors import ConflictError, NotFoundError, ValidationError


def create_user(
    *,
    full_name: str,
    email: str,
    password: str,
    role: str,
    roll_number: str | None = None,
    class_id: int | None = None,
    guardian_name: str | None = None,
    employee_code: str | None = None,
    department: str | None = None,
    specialization: str | None = None,
) -> User:
    if User.query.filter_by(email=email).first():
        raise ConflictError("An account with this email already exists.")

    user = User(full_name=full_name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    if role == "student":
        if not roll_number:
            raise ValidationError("'roll_number' is required for student accounts.")
        if Student.query.filter_by(roll_number=roll_number).first():
            raise ConflictError("This roll number is already in use.")
        db.session.add(
            Student(
                user_id=user.id,
                roll_number=roll_number,
                class_id=class_id,
                guardian_name=guardian_name,
            )
        )
    elif role == "teacher":
        if not employee_code:
            raise ValidationError("'employee_code' is required for teacher accounts.")
        if Teacher.query.filter_by(employee_code=employee_code).first():
            raise ConflictError("This employee code is already in use.")
        db.session.add(
            Teacher(
                user_id=user.id,
                employee_code=employee_code,
                department=department,
                specialization=specialization,
            )
        )

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise ConflictError("The account could not be created because of a duplicate value.") from None
    return user


def delete_user(user: User) -> None:
    db.session.delete(user)
    db.session.commit()


def get_user(user_id: int) -> User:
    user = db.session.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    return user
