"""Add user location columns

Revision ID: 004
Revises: 003
Create Date: 2026-06-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("longitude", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("city", sa.String(length=100), nullable=True))
    op.add_column("users", sa.Column("country", sa.String(length=2), nullable=True))
    op.add_column(
        "users",
        sa.Column("location_updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "location_updated_at")
    op.drop_column("users", "country")
    op.drop_column("users", "city")
    op.drop_column("users", "longitude")
    op.drop_column("users", "latitude")