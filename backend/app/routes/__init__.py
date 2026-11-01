"""Blueprint registration."""
from __future__ import annotations

from flask import Flask


def register_blueprints(app: Flask) -> None:
    from . import (
        academics,
        admin,
        analytics,
        auth,
        dl,
        feedback,
        recommendations,
        reports,
        students,
        teachers,
        teaching,
    )

    for module in (
        auth,
        admin,
        students,
        teachers,
        academics,
        dl,
        analytics,
        feedback,
        recommendations,
        reports,
        teaching,
    ):
        app.register_blueprint(module.bp)

    app.register_blueprint(academics.classes_bp)
    app.register_blueprint(academics.subjects_bp)
