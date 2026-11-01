"""Authentication / authorization helpers."""
from __future__ import annotations

from functools import wraps

from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from ..extensions import db
from ..models import Student, Teacher, User
from .errors import ForbiddenError, NotFoundError


def current_user() -> User:
    """Return the authenticated user for the active request.

    Deliberately not cached on ``g``: ``g`` is bound to the application context,
    which outlives a single request in embedded/test clients.
    """
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity)) if identity is not None else None
    if user is None or not user.is_active:
        raise NotFoundError("Authenticated user no longer exists or is inactive.")
    return user


def role_required(*roles: str):
    """Protect a route by role. Usage: @role_required("admin", "teacher")."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = current_user()
            if user.role not in roles:
                raise ForbiddenError(
                    f"This action requires one of the following roles: {', '.join(roles)}."
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def auth_required(fn):
    """Require any authenticated user."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        current_user()
        return fn(*args, **kwargs)

    return wrapper


def student_profile(user: User) -> Student:
    if not user.student_profile:
        raise NotFoundError("No student profile is linked to this account.")
    return user.student_profile


def teacher_profile(user: User) -> Teacher:
    if not user.teacher_profile:
        raise NotFoundError("No teacher profile is linked to this account.")
    return user.teacher_profile
