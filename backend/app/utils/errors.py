"""Typed application errors that map cleanly onto JSON responses."""
from __future__ import annotations


class APIError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str, status_code: int | None = None, code: str | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if code is not None:
            self.code = code

    def to_dict(self) -> dict:
        return {"error": self.code, "message": self.message}


class ValidationError(APIError):
    status_code = 422
    code = "validation_error"


class NotFoundError(APIError):
    status_code = 404
    code = "not_found"


class ForbiddenError(APIError):
    status_code = 403
    code = "forbidden"


class ConflictError(APIError):
    status_code = 409
    code = "conflict"


class ModelNotTrainedError(APIError):
    status_code = 503
    code = "model_not_trained"
