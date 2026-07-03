"""Add parlour_offers and cancellation_reasons; FK gaming_bookings.offer_id

Revision ID: 011
Revises: 010
Create Date: 2026-07-01

"""

from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CANCELLATION_REASONS = [
    ("Don't need play option", False, 1),
    ("Need help with location", False, 2),
    ("Found a better price", False, 3),
    ("Property issue", True, 4),
    ("Details mismatch", True, 5),
    ("Different issue", True, 6),
]


def upgrade() -> None:
    op.create_table(
        "parlour_offers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("parlour_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("code", sa.String(length=50), nullable=True),
        sa.Column(
            "discount_percent",
            sa.Numeric(precision=5, scale=2),
            server_default="0",
            nullable=False,
        ),
        sa.Column("discount_amount", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("min_hours", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("current_uses", sa.Integer(), server_default="0", nullable=False),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.ForeignKeyConstraint(["parlour_id"], ["gaming_places.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_parlour_offers_parlour_id", "parlour_offers", ["parlour_id"], unique=False)

    op.create_table(
        "cancellation_reasons",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("requires_detail", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    reasons_table = sa.table(
        "cancellation_reasons",
        sa.column("id", sa.UUID()),
        sa.column("label", sa.String()),
        sa.column("requires_detail", sa.Boolean()),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        reasons_table,
        [
            {
                "id": uuid.uuid4(),
                "label": label,
                "requires_detail": requires_detail,
                "sort_order": sort_order,
                "is_active": True,
            }
            for label, requires_detail, sort_order in CANCELLATION_REASONS
        ],
    )

    op.create_foreign_key(
        "fk_gaming_bookings_offer_id",
        "gaming_bookings",
        "parlour_offers",
        ["offer_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_gaming_bookings_offer_id", "gaming_bookings", type_="foreignkey")
    op.drop_table("cancellation_reasons")
    op.drop_index("ix_parlour_offers_parlour_id", table_name="parlour_offers")
    op.drop_table("parlour_offers")