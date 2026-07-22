"""Add users.bio column (model had it; migration was missing)

Revision ID: 019_users_bio
Revises: 018addremrec
Create Date: 2026-07-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "019_users_bio"
down_revision: str | None = "018addremrec"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT")


def downgrade() -> None:
    op.drop_column("users", "bio")
