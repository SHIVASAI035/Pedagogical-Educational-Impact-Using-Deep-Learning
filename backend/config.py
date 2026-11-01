"""Application configuration.

All secrets and connection details are read from environment variables so that
nothing sensitive is committed to source control. See ``.env.example``.
"""
from __future__ import annotations

import os
from datetime import timedelta

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _database_uri() -> str:
    """Build the SQLAlchemy URI.

    MySQL is the primary target. ``USE_SQLITE=1`` exists purely as a fallback so
    the project can boot on a machine without MySQL; the schema and queries are
    written to work on both engines.
    """
    if os.getenv("USE_SQLITE", "0") == "1":
        return f"sqlite:///{os.path.join(BASE_DIR, 'pedagogical_dev.sqlite3')}"

    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "pedagogical_education_db")
    return (
        f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"
    )


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "12"))
    )

    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}

    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ]

    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024

    ARTIFACT_DIR = os.path.join(BASE_DIR, "app", "deep_learning", "artifacts")
    DATASET_PATH = os.path.join(BASE_DIR, "app", "dataset", "student_performance.csv")
    MODEL_VERSION = "student-ann-v1"


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
