"""Small, dependency-free request validation helpers."""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Iterable

from flask import request

from .errors import ValidationError

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
ROLES = {"admin", "teacher", "student"}
ATTENDANCE_STATUS = {"present", "absent", "late"}


def payload() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    return data


def require_fields(data: dict, fields: Iterable[str]) -> None:
    missing = [field for field in fields if data.get(field) in (None, "")]
    if missing:
        raise ValidationError(f"Missing required field(s): {', '.join(missing)}.")


def as_str(value: Any, field: str, *, min_len: int = 1, max_len: int = 255) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"'{field}' must be a string.")
    value = value.strip()
    if len(value) < min_len:
        raise ValidationError(f"'{field}' must be at least {min_len} characters long.")
    if len(value) > max_len:
        raise ValidationError(f"'{field}' must be at most {max_len} characters long.")
    return value


def as_email(value: Any, field: str = "email") -> str:
    value = as_str(value, field, max_len=190).lower()
    if not EMAIL_RE.match(value):
        raise ValidationError("Please provide a valid email address.")
    return value


def as_role(value: Any) -> str:
    if value not in ROLES:
        raise ValidationError("'role' must be one of: admin, teacher, student.")
    return value


def as_password(value: Any) -> str:
    if not isinstance(value, str) or len(value) < 8:
        raise ValidationError("Password must be at least 8 characters long.")
    if len(value) > 128:
        raise ValidationError("Password must be at most 128 characters long.")
    return value


def as_float(value: Any, field: str, *, minimum: float | None = None,
             maximum: float | None = None) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"'{field}' must be a number.") from None
    if minimum is not None and number < minimum:
        raise ValidationError(f"'{field}' must be >= {minimum}.")
    if maximum is not None and number > maximum:
        raise ValidationError(f"'{field}' must be <= {maximum}.")
    return number


def as_int(value: Any, field: str, *, minimum: int | None = None,
           maximum: int | None = None) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"'{field}' must be an integer.") from None
    if minimum is not None and number < minimum:
        raise ValidationError(f"'{field}' must be >= {minimum}.")
    if maximum is not None and number > maximum:
        raise ValidationError(f"'{field}' must be <= {maximum}.")
    return number


def as_date(value: Any, field: str, *, default: date | None = None) -> date:
    if value in (None, "") and default is not None:
        return default
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        raise ValidationError(f"'{field}' must use the YYYY-MM-DD format.") from None


def as_status(value: Any) -> str:
    if value not in ATTENDANCE_STATUS:
        raise ValidationError("'status' must be one of: present, absent, late.")
    return value


def as_list(value: Any, field: str, *, minimum: int = 1, maximum: int = 50) -> list:
    if not isinstance(value, list) or not (minimum <= len(value) <= maximum):
        raise ValidationError(f"'{field}' must be a list with {minimum}-{maximum} items.")
    return value


def as_text(value: Any, field: str, *, max_len: int = 2000) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValidationError(f"'{field}' must be text.")
    value = value.strip()
    if len(value) > max_len:
        raise ValidationError(f"'{field}' must be at most {max_len} characters long.")
    return value
