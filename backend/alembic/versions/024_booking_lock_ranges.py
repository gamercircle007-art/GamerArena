"""Booking lock ranges: tstzrange + EXCLUDE so double booking is impossible.

Adds:
- gaming_bookings.during (tstzrange) — native overlap operator
- booking_unit_locks — one row per capacity unit with GiST EXCLUDE
- btree_gist for scalar equality in EXCLUDE

The EXCLUDE constraint is the correctness layer (SQLSTATE 23P01).
Redis locks remain a speed hint only.

Revision ID: 024_booking_lock_ranges
Revises: 023_discovery_read_model
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "024_booking_lock_ranges"
down_revision: str | None = "023_discovery_read_model"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LIVE_STATUSES = (
    "held",
    "payment_pending",
    "confirmed",
    "checked_in",
)


def upgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    op.add_column(
        "gaming_bookings",
        sa.Column("during_start", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "gaming_bookings",
        sa.Column("during_end", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "booking_unit_locks",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "booking_id",
            sa.Uuid(),
            sa.ForeignKey("gaming_bookings.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "parlor_id",
            sa.Uuid(),
            sa.ForeignKey("gaming_places.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("station_type", sa.String(length=20), nullable=False),
        sa.Column("unit_index", sa.SmallInteger(), nullable=False),
        sa.Column(
            "resource_id",
            sa.Uuid(),
            sa.ForeignKey("club_resources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("during_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("during_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_booking_unit_locks_lookup",
        "booking_unit_locks",
        ["parlor_id", "station_type", "is_active"],
    )

    if is_pg:
        op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")

        # Native tstzrange for overlap (&&) — kept in sync via trigger from during_* columns
        op.execute(
            """
            ALTER TABLE gaming_bookings
            ADD COLUMN IF NOT EXISTS during tstzrange
            """
        )
        op.execute(
            """
            ALTER TABLE booking_unit_locks
            ADD COLUMN IF NOT EXISTS during tstzrange
            """
        )

        # Backfill from legacy date + time (interpret as Asia/Kolkata wall clock → timestamptz)
        op.execute(
            """
            UPDATE gaming_bookings
            SET
              during_start = (
                (slot_date + start_time) AT TIME ZONE 'Asia/Kolkata'
              ),
              during_end = (
                (slot_date + COALESCE(end_time, start_time + INTERVAL '1 hour'))
                AT TIME ZONE 'Asia/Kolkata'
              )
            WHERE slot_date IS NOT NULL
              AND start_time IS NOT NULL
              AND during_start IS NULL
            """
        )
        op.execute(
            """
            UPDATE gaming_bookings
            SET during = tstzrange(during_start, during_end, '[)')
            WHERE during_start IS NOT NULL
              AND during_end IS NOT NULL
              AND during IS NULL
            """
        )

        op.execute(
            """
            CREATE OR REPLACE FUNCTION gaming_bookings_sync_during()
            RETURNS trigger AS $$
            BEGIN
              IF NEW.during_start IS NOT NULL AND NEW.during_end IS NOT NULL THEN
                NEW.during := tstzrange(NEW.during_start, NEW.during_end, '[)');
              ELSIF NEW.slot_date IS NOT NULL AND NEW.start_time IS NOT NULL THEN
                NEW.during_start := (NEW.slot_date + NEW.start_time) AT TIME ZONE 'Asia/Kolkata';
                NEW.during_end := (
                  NEW.slot_date + COALESCE(
                    NEW.end_time,
                    NEW.start_time + make_interval(hours => COALESCE(NEW.duration_hours, 1))
                  )
                ) AT TIME ZONE 'Asia/Kolkata';
                NEW.during := tstzrange(NEW.during_start, NEW.during_end, '[)');
              END IF;
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
            """
        )
        op.execute("DROP TRIGGER IF EXISTS trg_gaming_bookings_sync_during ON gaming_bookings")
        op.execute(
            """
            CREATE TRIGGER trg_gaming_bookings_sync_during
            BEFORE INSERT OR UPDATE OF slot_date, start_time, end_time,
              duration_hours, during_start, during_end
            ON gaming_bookings
            FOR EACH ROW EXECUTE FUNCTION gaming_bookings_sync_during()
            """
        )

        op.execute(
            """
            CREATE OR REPLACE FUNCTION booking_unit_locks_sync_during()
            RETURNS trigger AS $$
            BEGIN
              NEW.during := tstzrange(NEW.during_start, NEW.during_end, '[)');
              RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
            """
        )
        op.execute("DROP TRIGGER IF EXISTS trg_booking_unit_locks_sync_during ON booking_unit_locks")
        op.execute(
            """
            CREATE TRIGGER trg_booking_unit_locks_sync_during
            BEFORE INSERT OR UPDATE OF during_start, during_end
            ON booking_unit_locks
            FOR EACH ROW EXECUTE FUNCTION booking_unit_locks_sync_during()
            """
        )

        # --- THE constraint that makes double booking impossible ---
        # Two live locks for the same parlor/station/unit cannot overlap in time.
        op.execute(
            f"""
            ALTER TABLE booking_unit_locks
            ADD CONSTRAINT excl_booking_unit_locks_overlap
            EXCLUDE USING gist (
              parlor_id WITH =,
              station_type WITH =,
              unit_index WITH =,
              during WITH &&
            )
            WHERE (is_active)
            """
        )

        # Physical resource overlap (when a specific PC/console is assigned)
        op.execute(
            """
            ALTER TABLE booking_unit_locks
            ADD CONSTRAINT excl_booking_unit_locks_resource
            EXCLUDE USING gist (
              resource_id WITH =,
              during WITH &&
            )
            WHERE (is_active AND resource_id IS NOT NULL)
            """
        )

        # Optional: resource-level exclude on bookings themselves when resource_id set
        op.execute(
            """
            ALTER TABLE gaming_bookings
            ADD CONSTRAINT excl_gaming_bookings_resource_during
            EXCLUDE USING gist (
              resource_id WITH =,
              during WITH &&
            )
            WHERE (
              resource_id IS NOT NULL
              AND during IS NOT NULL
              AND booking_status IN ('held','payment_pending','confirmed','checked_in')
            )
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    is_pg = bind.dialect.name == "postgresql"

    if is_pg:
        op.execute(
            "ALTER TABLE gaming_bookings DROP CONSTRAINT IF EXISTS excl_gaming_bookings_resource_during"
        )
        op.execute(
            "ALTER TABLE booking_unit_locks DROP CONSTRAINT IF EXISTS excl_booking_unit_locks_resource"
        )
        op.execute(
            "ALTER TABLE booking_unit_locks DROP CONSTRAINT IF EXISTS excl_booking_unit_locks_overlap"
        )
        op.execute("DROP TRIGGER IF EXISTS trg_booking_unit_locks_sync_during ON booking_unit_locks")
        op.execute("DROP TRIGGER IF EXISTS trg_gaming_bookings_sync_during ON gaming_bookings")
        op.execute("DROP FUNCTION IF EXISTS booking_unit_locks_sync_during()")
        op.execute("DROP FUNCTION IF EXISTS gaming_bookings_sync_during()")
        op.execute("ALTER TABLE booking_unit_locks DROP COLUMN IF EXISTS during")
        op.execute("ALTER TABLE gaming_bookings DROP COLUMN IF EXISTS during")

    op.drop_table("booking_unit_locks")
    op.drop_column("gaming_bookings", "during_end")
    op.drop_column("gaming_bookings", "during_start")
