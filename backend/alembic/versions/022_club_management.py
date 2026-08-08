"""Club Management: zones, resources, pricing rules, promotions, CRM, occupancy rollups

Additive only. Creates six new club-scoped tables and appends owner-ops lifecycle
columns to gaming_bookings. Nothing existing is dropped or renamed, and downgrade()
fully reverses upgrade() (unlike 021, whose downgrade left its gaming_bookings
ALTERs in place).

Enum-ish columns are String + CHECK rather than native PG enum types: reversible in
one step, and keeps the models loadable on the SQLite dev database that
scripts/run_dev.py builds via metadata.create_all.

Revision ID: 022_club_management
Revises: 021_cashfree_slots
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "022_club_management"
down_revision: str | None = "021_cashfree_slots"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


#: Kept as literals rather than importing app.domains.club_ops.enums so this migration
#: stays a frozen snapshot of the schema at this revision, per Alembic convention.
RESOURCE_TYPES = "'seat', 'pc', 'console', 'ps5', 'pool', 'vr', 'other'"
RESOURCE_STATUSES = "'available', 'occupied', 'reserved', 'maintenance', 'offline'"
PRICING_SCOPES = "'club', 'resource_type', 'zone', 'resource'"
PROMO_TYPES = "'percent', 'flat', 'happy_hour', 'first_visit', 'loyalty', 'code'"
ROLLUP_GRAINS = "'club', 'resource_type', 'zone', 'resource'"

_BOOKING_COLUMNS = (
    "resource_id",
    "club_customer_id",
    "club_promotion_id",
    "is_walk_in",
    "checked_in_at",
    "checked_out_at",
    "extended_hours",
    "no_show_at",
    "cancelled_by",
    "club_discount_paise",
)


def upgrade() -> None:
    op.create_table(
        "club_zones",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "parlor_id",
            sa.Uuid(),
            sa.ForeignKey("gaming_places.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("parlor_id", "name", name="uq_club_zones_parlor_name"),
    )
    op.create_index("ix_club_zones_parlor_active", "club_zones", ["parlor_id", "is_active"])

    op.create_table(
        "club_resources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "parlor_id",
            sa.Uuid(),
            sa.ForeignKey("gaming_places.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "zone_id",
            sa.Uuid(),
            sa.ForeignKey("club_zones.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("resource_type", sa.String(20), nullable=False, server_default="pc"),
        sa.Column("label", sa.String(60), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="available"),
        sa.Column("specs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("hourly_rate_override_paise", sa.Integer(), nullable=True),
        sa.Column("layout_x", sa.Integer(), nullable=True),
        sa.Column("layout_y", sa.Integer(), nullable=True),
        sa.Column("status_note", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("parlor_id", "label", name="uq_club_resources_parlor_label"),
        sa.CheckConstraint(f"resource_type IN ({RESOURCE_TYPES})", name="ck_club_resources_type"),
        sa.CheckConstraint(f"status IN ({RESOURCE_STATUSES})", name="ck_club_resources_status"),
        sa.CheckConstraint(
            "hourly_rate_override_paise IS NULL OR hourly_rate_override_paise >= 0",
            name="ck_club_resources_rate",
        ),
    )
    op.create_index(
        "ix_club_resources_parlor_type", "club_resources", ["parlor_id", "resource_type", "is_active"]
    )
    op.create_index("ix_club_resources_parlor_status", "club_resources", ["parlor_id", "status"])

    op.create_table(
        "club_pricing_rules",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "parlor_id",
            sa.Uuid(),
            sa.ForeignKey("gaming_places.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("scope", sa.String(20), nullable=False, server_default="club"),
        sa.Column("scope_value", sa.String(64), nullable=False, server_default=""),
        sa.Column("base_rate_paise", sa.Integer(), nullable=False),
        sa.Column("time_slabs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("day_of_week_overrides", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("package_defs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(f"scope IN ({PRICING_SCOPES})", name="ck_club_pricing_rules_scope"),
        sa.CheckConstraint("base_rate_paise >= 0", name="ck_club_pricing_rules_base_rate"),
    )
    op.create_index(
        "ix_club_pricing_rules_lookup", "club_pricing_rules", ["parlor_id", "is_active", "scope"]
    )

    op.create_table(
        "club_promotions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "parlor_id",
            sa.Uuid(),
            sa.ForeignKey("gaming_places.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("promo_type", sa.String(20), nullable=False),
        sa.Column("percent_bps", sa.Integer(), nullable=True),
        sa.Column("flat_paise", sa.Integer(), nullable=True),
        sa.Column("code", sa.String(40), nullable=True),
        sa.Column("max_discount_paise", sa.Integer(), nullable=True),
        sa.Column("min_amount_paise", sa.Integer(), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("happy_hour_start", sa.Time(), nullable=True),
        sa.Column("happy_hour_end", sa.Time(), nullable=True),
        sa.Column("usage_limit", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "applicable_resource_types", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("min_loyalty_points", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "disabled_by_platform", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("disabled_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("parlor_id", "code", name="uq_club_promotions_parlor_code"),
        sa.CheckConstraint(f"promo_type IN ({PROMO_TYPES})", name="ck_club_promotions_type"),
        sa.CheckConstraint(
            "percent_bps IS NULL OR (percent_bps > 0 AND percent_bps <= 10000)",
            name="ck_club_promotions_percent",
        ),
        sa.CheckConstraint("flat_paise IS NULL OR flat_paise > 0", name="ck_club_promotions_flat"),
        sa.CheckConstraint(
            "percent_bps IS NOT NULL OR flat_paise IS NOT NULL",
            name="ck_club_promotions_has_value",
        ),
        sa.CheckConstraint("used_count >= 0", name="ck_club_promotions_used_count"),
    )
    op.create_index(
        "ix_club_promotions_active", "club_promotions", ["parlor_id", "is_active", "valid_to"]
    )

    op.create_table(
        "club_customers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "parlor_id",
            sa.Uuid(),
            sa.ForeignKey("gaming_places.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
            index=True,
        ),
        sa.Column("display_name", sa.String(120), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("visit_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_spend_paise", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_visit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("loyalty_points", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_banned", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("ban_reason", sa.Text(), nullable=True),
        sa.Column("banned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("platform_flagged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("platform_flag_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("parlor_id", "user_id", name="uq_club_customers_parlor_user"),
        sa.CheckConstraint("visit_count >= 0", name="ck_club_customers_visit_count"),
        sa.CheckConstraint("total_spend_paise >= 0", name="ck_club_customers_spend"),
    )
    op.create_index(
        "ix_club_customers_parlor_last_visit", "club_customers", ["parlor_id", "last_visit_at"]
    )
    op.create_index("ix_club_customers_parlor_phone", "club_customers", ["parlor_id", "phone"])

    op.create_table(
        "club_customer_notes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "club_customer_id",
            sa.Uuid(),
            sa.ForeignKey("club_customers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("author_id", sa.Uuid(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index(
        "ix_club_customer_notes_customer", "club_customer_notes", ["club_customer_id", "created_at"]
    )

    op.create_table(
        "club_occupancy_rollups",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "parlor_id",
            sa.Uuid(),
            sa.ForeignKey("gaming_places.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("bucket_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("grain", sa.String(20), nullable=False),
        sa.Column("grain_key", sa.String(64), nullable=False, server_default=""),
        sa.Column("ist_hour", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("ist_weekday", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("occupied_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("capacity_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("booking_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("no_show_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_paise", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("commission_paise", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        # This is what makes the Celery rollup task idempotent — it upserts on this key.
        sa.UniqueConstraint(
            "parlor_id", "bucket_start", "grain", "grain_key", name="uq_club_rollup_bucket"
        ),
        sa.CheckConstraint(f"grain IN ({ROLLUP_GRAINS})", name="ck_club_rollup_grain"),
        sa.CheckConstraint("occupied_minutes >= 0", name="ck_club_rollup_occupied"),
        sa.CheckConstraint("capacity_minutes >= 0", name="ck_club_rollup_capacity"),
    )
    op.create_index(
        "ix_club_rollup_range", "club_occupancy_rollups", ["parlor_id", "grain", "bucket_start"]
    )

    # --- Additive owner-ops lifecycle columns on the EXISTING bookings table ---
    op.add_column(
        "gaming_bookings",
        sa.Column(
            "resource_id",
            sa.Uuid(),
            sa.ForeignKey("club_resources.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "gaming_bookings",
        sa.Column(
            "club_customer_id",
            sa.Uuid(),
            sa.ForeignKey("club_customers.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "gaming_bookings",
        sa.Column(
            "club_promotion_id",
            sa.Uuid(),
            sa.ForeignKey("club_promotions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "gaming_bookings",
        sa.Column("is_walk_in", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "gaming_bookings", sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "gaming_bookings", sa.Column("checked_out_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "gaming_bookings", sa.Column("extended_hours", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column(
        "gaming_bookings", sa.Column("no_show_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("gaming_bookings", sa.Column("cancelled_by", sa.String(20), nullable=True))
    op.add_column(
        "gaming_bookings",
        sa.Column("club_discount_paise", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_index("ix_gaming_bookings_resource", "gaming_bookings", ["resource_id"])
    op.create_index("ix_gaming_bookings_club_customer", "gaming_bookings", ["club_customer_id"])
    # Drives the owner "live now" and day/week calendar queries.
    op.create_index(
        "ix_gaming_bookings_owner_calendar",
        "gaming_bookings",
        ["parlour_id", "slot_date", "booking_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_gaming_bookings_owner_calendar", table_name="gaming_bookings")
    op.drop_index("ix_gaming_bookings_club_customer", table_name="gaming_bookings")
    op.drop_index("ix_gaming_bookings_resource", table_name="gaming_bookings")
    for column in _BOOKING_COLUMNS:
        op.drop_column("gaming_bookings", column)

    op.drop_index("ix_club_rollup_range", table_name="club_occupancy_rollups")
    op.drop_table("club_occupancy_rollups")

    op.drop_index("ix_club_customer_notes_customer", table_name="club_customer_notes")
    op.drop_table("club_customer_notes")

    op.drop_index("ix_club_customers_parlor_phone", table_name="club_customers")
    op.drop_index("ix_club_customers_parlor_last_visit", table_name="club_customers")
    op.drop_table("club_customers")

    op.drop_index("ix_club_promotions_active", table_name="club_promotions")
    op.drop_table("club_promotions")

    op.drop_index("ix_club_pricing_rules_lookup", table_name="club_pricing_rules")
    op.drop_table("club_pricing_rules")

    op.drop_index("ix_club_resources_parlor_status", table_name="club_resources")
    op.drop_index("ix_club_resources_parlor_type", table_name="club_resources")
    op.drop_table("club_resources")

    op.drop_index("ix_club_zones_parlor_active", table_name="club_zones")
    op.drop_table("club_zones")
