"""Add gaming_slots and gaming_bookings tables for OYO-style parlor booking

Revision ID: 010
Revises: 009
Create Date: 2026-07-01

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gaming_slots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("parlour_id", sa.UUID(), nullable=False),
        sa.Column("parlour_game_id", sa.UUID(), nullable=True),
        sa.Column("slot_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("price_per_hour", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("original_price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("max_players", sa.Integer(), server_default="1", nullable=False),
        sa.Column("current_bookings", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_available", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["parlour_id"], ["gaming_places.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_gaming_slots_parlour_id_slot_date",
        "gaming_slots",
        ["parlour_id", "slot_date"],
        unique=False,
    )

    op.create_table(
        "gaming_bookings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("booking_ref", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("parlour_id", sa.UUID(), nullable=False),
        sa.Column("slot_id", sa.UUID(), nullable=True),
        sa.Column("offer_id", sa.UUID(), nullable=True),
        sa.Column("guest_name", sa.String(length=100), nullable=True),
        sa.Column("num_players", sa.Integer(), server_default="1", nullable=False),
        sa.Column("slot_date", sa.Date(), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("hours_booked", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("price_per_hour", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("total_price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("tax_amount", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "discount_amount",
            sa.Numeric(precision=10, scale=2),
            server_default="0",
            nullable=False,
        ),
        sa.Column("final_price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column(
            "payment_mode",
            sa.String(length=30),
            server_default="pay_at_parlor",
            nullable=False,
        ),
        sa.Column(
            "payment_status",
            sa.String(length=20),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("payment_id", sa.String(length=100), nullable=True),
        sa.Column(
            "booking_status",
            sa.String(length=20),
            server_default="confirmed",
            nullable=False,
        ),
        sa.Column("cancellation_reason", sa.String(length=100), nullable=True),
        sa.Column("cancellation_detail", sa.Text(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "refund_amount",
            sa.Numeric(precision=10, scale=2),
            server_default="0",
            nullable=False,
        ),
        sa.Column("refund_status", sa.String(length=20), nullable=True),
        sa.Column("free_cancellation_before", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_non_refundable", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("gc_points_earned", sa.Integer(), server_default="0", nullable=False),
        sa.Column("contact_email", sa.String(length=200), nullable=True),
        sa.Column("contact_phone", sa.String(length=20), nullable=True),
        sa.Column("gstin", sa.String(length=20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["parlour_id"], ["gaming_places.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["slot_id"], ["gaming_slots.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_ref", name="uq_gaming_bookings_booking_ref"),
    )
    op.create_index("ix_gaming_bookings_user_id", "gaming_bookings", ["user_id"], unique=False)
    op.create_index("ix_gaming_bookings_parlour_id", "gaming_bookings", ["parlour_id"], unique=False)
    op.create_index("ix_gaming_bookings_booking_status", "gaming_bookings", ["booking_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_gaming_bookings_booking_status", table_name="gaming_bookings")
    op.drop_index("ix_gaming_bookings_parlour_id", table_name="gaming_bookings")
    op.drop_index("ix_gaming_bookings_user_id", table_name="gaming_bookings")
    op.drop_table("gaming_bookings")

    op.drop_index("ix_gaming_slots_parlour_id_slot_date", table_name="gaming_slots")
    op.drop_table("gaming_slots")