"""Cashfree + stations/hours/holds/ledger/webhooks/audit

Revision ID: 021_cashfree_slots
Revises: 020_admin_parlor_soft_delete
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "021_cashfree_slots"
down_revision: str | None = "020_admin_parlor_soft_delete"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "parlor_stations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("parlor_id", sa.Uuid(), sa.ForeignKey("gaming_places.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("station_type", sa.String(20), nullable=False),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("hourly_price_paise", sa.Integer(), nullable=False, server_default="9900"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("specs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("parlor_id", "station_type", name="uq_parlor_stations_type"),
        sa.CheckConstraint("total_count > 0", name="ck_parlor_stations_count"),
        sa.CheckConstraint("hourly_price_paise >= 0", name="ck_parlor_stations_price"),
    )

    op.create_table(
        "parlor_hours",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("parlor_id", sa.Uuid(), sa.ForeignKey("gaming_places.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("open_time", sa.Time(), nullable=False),
        sa.Column("close_time", sa.Time(), nullable=False),
        sa.UniqueConstraint("parlor_id", "weekday", "open_time", name="uq_parlor_hours_shift"),
    )

    op.create_table(
        "parlor_closures",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("parlor_id", sa.Uuid(), sa.ForeignKey("gaming_places.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.UniqueConstraint("parlor_id", "date", name="uq_parlor_closures_date"),
    )

    # Extend gaming_bookings for Cashfree + virtual booking fields
    op.execute("""
    DO $$ BEGIN
      ALTER TABLE gaming_bookings ADD COLUMN IF NOT EXISTS station_type VARCHAR(20);
      ALTER TABLE gaming_bookings ADD COLUMN IF NOT EXISTS duration_hours SMALLINT;
      ALTER TABLE gaming_bookings ADD COLUMN IF NOT EXISTS units SMALLINT DEFAULT 1;
      ALTER TABLE gaming_bookings ADD COLUMN IF NOT EXISTS amount_paise INTEGER;
      ALTER TABLE gaming_bookings ADD COLUMN IF NOT EXISTS commission_paise INTEGER DEFAULT 0;
      ALTER TABLE gaming_bookings ADD COLUMN IF NOT EXISTS cf_order_id VARCHAR(100);
      ALTER TABLE gaming_bookings ADD COLUMN IF NOT EXISTS payment_session_id VARCHAR(200);
      ALTER TABLE gaming_bookings ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(100);
      ALTER TABLE gaming_bookings ADD COLUMN IF NOT EXISTS hold_expires_at TIMESTAMPTZ;
      ALTER TABLE gaming_bookings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();
    END $$;
    """)
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_gaming_bookings_cf_order ON gaming_bookings (cf_order_id) WHERE cf_order_id IS NOT NULL")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_gaming_bookings_idem ON gaming_bookings (idempotency_key) WHERE idempotency_key IS NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_gaming_bookings_slot_lookup ON gaming_bookings (parlour_id, station_type, slot_date, booking_status)")

    op.create_table(
        "booking_holds",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("booking_id", sa.Uuid(), sa.ForeignKey("gaming_bookings.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("parlor_id", sa.Uuid(), sa.ForeignKey("gaming_places.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("station_type", sa.String(20), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("duration_hours", sa.SmallInteger(), nullable=False),
        sa.Column("units", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("released", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_booking_holds_lookup ON booking_holds (parlor_id, station_type, date, expires_at)")

    op.create_table(
        "payment_ledger",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("booking_id", sa.Uuid(), sa.ForeignKey("gaming_bookings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("entry_type", sa.String(30), nullable=False),
        sa.Column("amount_paise", sa.Integer(), nullable=False),
        sa.Column("cf_reference", sa.String(100), nullable=True),
        sa.Column("cf_event_id", sa.String(100), nullable=True),
        sa.Column("balance_direction", sa.String(10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_payment_ledger_event ON payment_ledger (cf_event_id) WHERE cf_event_id IS NOT NULL")

    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("provider", sa.String(30), nullable=False, server_default="cashfree"),
        sa.Column("event_id", sa.String(120), nullable=False, unique=True),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("signature_valid", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("processed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "booking_audit",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("booking_id", sa.Uuid(), sa.ForeignKey("gaming_bookings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("from_status", sa.String(30), nullable=True),
        sa.Column("to_status", sa.String(30), nullable=False),
        sa.Column("actor", sa.String(30), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "reconciliation_issues",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("booking_id", sa.Uuid(), nullable=True),
        sa.Column("cf_reference", sa.String(100), nullable=True),
        sa.Column("issue_type", sa.String(50), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("reconciliation_issues")
    op.drop_table("booking_audit")
    op.drop_table("webhook_events")
    op.drop_table("payment_ledger")
    op.drop_table("booking_holds")
    op.drop_table("parlor_closures")
    op.drop_table("parlor_hours")
    op.drop_table("parlor_stations")
