"""Extend gaming_place_extensions, add parlour_ratings

Revision ID: 013
Revises: 012
Create Date: 2026-07-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if not _table_exists("gaming_place_extensions"):
        op.create_table(
            "gaming_place_extensions",
            sa.Column("gaming_place_id", sa.UUID(), nullable=False),
            sa.Column("owner_id", sa.UUID(), nullable=True),
            sa.Column("follower_count", sa.Integer(), server_default="0", nullable=False),
            sa.Column("post_count", sa.Integer(), server_default="0", nullable=False),
            sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["gaming_place_id"], ["gaming_places.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("gaming_place_id"),
        )
        op.create_index(
            "ix_gaming_place_extensions_owner_id",
            "gaming_place_extensions",
            ["owner_id"],
            unique=False,
        )

    ext_columns = {
        "price_per_hour": sa.Numeric(precision=10, scale=2),
        "original_price": sa.Numeric(precision=10, scale=2),
        "discount_percent": sa.Numeric(precision=5, scale=2),
        "base_tax_rate": sa.Numeric(precision=5, scale=2),
        "equipment_rating": sa.Numeric(precision=3, scale=2),
        "staff_rating": sa.Numeric(precision=3, scale=2),
        "checkin_rating": sa.Numeric(precision=3, scale=2),
        "is_wizard_enabled": sa.Boolean(),
        "is_couples_allowed": sa.Boolean(),
    }
    for col_name, col_type in ext_columns.items():
        if col_name in ("is_wizard_enabled", "is_couples_allowed"):
            op.add_column(
                "gaming_place_extensions",
                sa.Column(
                    col_name,
                    col_type,
                    server_default=sa.text("false"),
                    nullable=False,
                ),
            )
        elif col_name == "base_tax_rate":
            op.add_column(
                "gaming_place_extensions",
                sa.Column(
                    col_name,
                    col_type,
                    server_default="18",
                    nullable=False,
                ),
            )
        else:
            op.add_column(
                "gaming_place_extensions",
                sa.Column(col_name, col_type, nullable=True),
            )

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        review_photos_type = postgresql.ARRAY(sa.Text())
    else:
        review_photos_type = sa.JSON()

    op.create_table(
        "parlour_ratings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("gaming_place_id", sa.UUID(), nullable=False),
        sa.Column("rating", sa.Numeric(precision=3, scale=2), nullable=False),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column("equipment_rating", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("staff_rating", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("location_rating", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("cleanliness_rating", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column("checkin_rating", sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column(
            "is_verified_stay",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("review_photos", review_photos_type, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["gaming_place_id"], ["gaming_places.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "gaming_place_id", name="uq_parlour_ratings_user_place"),
    )
    op.create_index(
        "ix_parlour_ratings_gaming_place_id",
        "parlour_ratings",
        ["gaming_place_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_parlour_ratings_gaming_place_id", table_name="parlour_ratings")
    op.drop_table("parlour_ratings")

    for col in (
        "is_couples_allowed",
        "is_wizard_enabled",
        "checkin_rating",
        "staff_rating",
        "equipment_rating",
        "base_tax_rate",
        "discount_percent",
        "original_price",
        "price_per_hour",
    ):
        op.drop_column("gaming_place_extensions", col)