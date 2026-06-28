"""create users and notes tables

Revision ID: f4311be9dd73
Revises:
Create Date: 2026-06-28 17:29:25.356663

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f4311be9dd73'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the users and notes tables (matches the former init_db SQL)."""
    op.execute(
        """
        CREATE TABLE users (
            id   SERIAL PRIMARY KEY,
            name TEXT UNIQUE NOT NULL
        )
        """
    )
    op.execute(
        """
        CREATE TABLE notes (
            id         SERIAL PRIMARY KEY,
            user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            note_date  DATE NOT NULL,
            content    TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX idx_notes_user_date ON notes(user_id, note_date)")


def downgrade() -> None:
    """Drop the notes and users tables."""
    op.execute("DROP TABLE IF EXISTS notes")
    op.execute("DROP TABLE IF EXISTS users")
