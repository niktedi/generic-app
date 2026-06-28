"""Shared test fixtures.

Integration tests run against a real PostgreSQL (the same connection the app
uses, configured via env vars — point DB_NAME at a throwaway DB like
`calendar_test` in CI). The autouse fixture guarantees the schema exists and
the tables are empty before each test so tests stay isolated.
"""

import pytest

from app import db


@pytest.fixture(autouse=True)
def clean_db():
    """Ensure schema exists and tables are empty before each test."""
    # The test database is disposable, so creating the schema directly here is
    # fine. When CI applies Alembic migrations before the run, this CREATE is a
    # harmless no-op thanks to IF NOT EXISTS.
    with db.get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id   SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS notes (
                id         SERIAL PRIMARY KEY,
                user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                note_date  DATE NOT NULL,
                content    TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        cur.execute("TRUNCATE notes, users RESTART IDENTITY CASCADE")
    yield
