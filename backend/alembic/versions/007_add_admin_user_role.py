"""Add admin value to user_role enum

Revision ID: 007
Revises: 006
Create Date: 2026-06-27

"""
from typing import Sequence, Union

from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'admin'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values safely.
    pass