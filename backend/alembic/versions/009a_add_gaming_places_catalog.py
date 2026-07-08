"""Add gaming_places catalog table synced from projectX

Revision ID: 009a
Revises: 009
Create Date: 2026-07-03

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009a"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gaming_places",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("google_place_id", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city_id", sa.UUID(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("user_ratings_total", sa.Integer(), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("google_maps_url", sa.String(length=500), nullable=True),
        sa.Column("business_status", sa.String(length=50), nullable=True),
        sa.Column("primary_type", sa.String(length=100), nullable=True),
        sa.Column("types", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("opening_hours", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("image_url", sa.String(length=1000), nullable=True),
        sa.Column("photo_name", sa.String(length=500), nullable=True),
        sa.Column("photos", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("google_place_id"),
    )
    op.create_index("ix_gaming_places_google_place_id", "gaming_places", ["google_place_id"])
    op.create_index("ix_gaming_places_city_id", "gaming_places", ["city_id"])


def downgrade() -> None:
    op.drop_index("ix_gaming_places_city_id", table_name="gaming_places")
    op.drop_index("ix_gaming_places_google_place_id", table_name="gaming_places")
    op.drop_table("gaming_places")