"""Application factory for the Pedagogical & Educational Impact platform."""
from __future__ import annotations

import logging
import os

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from config import Config

from .extensions import cors, db, jwt
from .utils.errors import APIError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Make sure the artifact/dataset folders exist on first boot.
    os.makedirs(app.config["ARTIFACT_DIR"], exist_ok=True)
    os.makedirs(os.path.dirname(app.config["DATASET_PATH"]), exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    _register_jwt_handlers()
    _register_error_handlers(app)

    from .routes import register_blueprints

    register_blueprints(app)

    @app.get("/api/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "service": "pedagogical-education-api",
                "database": db.engine.url.get_backend_name(),
            }
        )

    # Auto-create tables for a smooth first run. `database/schema.sql` remains
    # the authoritative MySQL definition for a controlled deployment.
    with app.app_context():
        from . import models  # noqa: F401  (register metadata)

        db.create_all()

    return app


def _register_jwt_handlers() -> None:
    @jwt.unauthorized_loader
    def missing_token(reason: str):
        return jsonify({"error": "unauthorized", "message": "Authentication is required."}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason: str):
        return jsonify({"error": "invalid_token", "message": "The access token is invalid."}), 422

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return jsonify({"error": "token_expired", "message": "The access token has expired."}), 401


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(APIError)
    def handle_api_error(error: APIError):
        return jsonify(error.to_dict()), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        return (
            jsonify(
                {
                    "error": error.name.lower().replace(" ", "_"),
                    "message": error.description,
                }
            ),
            error.code,
        )

    @app.errorhandler(Exception)
    def handle_unexpected(error: Exception):
        logger.exception("Unhandled error: %s", error)
        return (
            jsonify(
                {
                    "error": "internal_error",
                    "message": "An unexpected error occurred. Please try again.",
                }
            ),
            500,
        )
