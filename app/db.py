"""
PostgreSQL access layer for the calendar app.

Connection settings come from the .env file (see .env.example). We use
pg8000 — a pure-Python PostgreSQL driver — so the app runs on any platform
and Python version without needing libpq or compiled wheels.

This module is deliberately kept separate from FastAPI routing (main.py):
it owns the schema and all SQL, exposing small repository functions that
the route handlers call. That keeps the HTTP layer thin and testable.
"""

import os
from contextlib import contextmanager

import pg8000.dbapi
from dotenv import load_dotenv

load_dotenv()


def _conn_kwargs() -> dict:
    """Build pg8000 connection kwargs from environment variables."""
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "calendar"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
    }


@contextmanager
def get_conn():
    """
    Yield a database connection, committing on success and rolling back on
    error. The connection is always closed afterwards.
    """
    conn = pg8000.dbapi.connect(**_conn_kwargs())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they do not exist yet. Safe to run on every startup."""
    with get_conn() as conn:
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
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notes_user_date ON notes(user_id, note_date)")


def get_or_create_user(name: str) -> dict:
    """
    Return the user with the given name, creating it if it does not exist.
    Authentication is intentionally absent — the name alone identifies a user.
    """
    name = name.strip()
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM users WHERE name = %s", (name,))
        row = cur.fetchone()
        if row is None:
            cur.execute("INSERT INTO users (name) VALUES (%s) RETURNING id, name", (name,))
            row = cur.fetchone()
        return {"id": row[0], "name": row[1]}


def get_notes_for_month(user_id: int, year: int, month: int) -> list[dict]:
    """Return all notes for a user within the given calendar month."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, note_date, content
            FROM notes
            WHERE user_id = %s
              AND EXTRACT(YEAR FROM note_date) = %s
              AND EXTRACT(MONTH FROM note_date) = %s
            ORDER BY note_date, created_at, id
            """,
            (user_id, year, month),
        )
        return [
            {"id": r[0], "date": r[1].isoformat(), "content": r[2]} for r in cur.fetchall()
        ]


def add_note(user_id: int, note_date: str, content: str) -> dict:
    """Insert a single note block for a user on a given date (YYYY-MM-DD)."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO notes (user_id, note_date, content)
            VALUES (%s, %s, %s)
            RETURNING id, note_date, content
            """,
            (user_id, note_date, content.strip()),
        )
        r = cur.fetchone()
        return {"id": r[0], "date": r[1].isoformat(), "content": r[2]}


def delete_note(note_id: int, user_id: int) -> bool:
    """
    Delete a note by id, scoped to its owner. The user_id filter ensures a
    user can only delete their own notes. Returns True if a row was removed.
    """
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM notes WHERE id = %s AND user_id = %s", (note_id, user_id))
        return cur.rowcount > 0
