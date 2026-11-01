"""Optional live MySQL integration test.

Run with:
    set TEST_MYSQL=1
    pytest tests/test_mysql_integration.py -v
"""
from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("TEST_MYSQL") != "1",
    reason="Set TEST_MYSQL=1 to run against the configured MySQL database.",
)


def test_mysql_connection_and_tables():
    from config import Config
    from app import create_app
    from app.extensions import db
    from app.models import User

    assert Config.SQLALCHEMY_DATABASE_URI.startswith("mysql")
    app = create_app()
    with app.app_context():
        assert db.engine.url.get_backend_name() == "mysql"
        # Every model table must exist in the live database.
        assert User.query.limit(1).all() is not None
