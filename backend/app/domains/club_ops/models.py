"""Club Management ORM models — resources, zones, pricing, promotions, CRM, rollups.

Conventions held to here:
- Every table is club-scoped via `parlor_id` -> `gaming_places.id` (the real venue
  identity in this codebase; `gaming_place_extensions.owner_id` carries ownership).
  New tables deliberately do NOT reference the legacy `parlors` table, which is
  superseded dead code (`app/domains/parlor/models.py`).
- All currency is integer **paise**. No Numeric/float money columns in this module.
- JSON columns use `PortableJSON` so they are JSONB on PostgreSQL and JSON on the
  SQLite dev database.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, time

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import PortableJSON
from app.domains.club_ops.enums import (
    PricingScope,
    PromotionType,
    ResourceStatus,
    ResourceType,
    RollupGrain,
)


def _values(enum_cls) -> str:
    """Render an enum's values as a SQL IN-list for a CHECK constraint."""
    return ", ".join(f"'{m.value}'" for m in enum_cls)


class ClubZone(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A named grouping of resources within a club ("PS5 Zone", "PC Arena")."""

    __tablename__ = "club_zones"
    __table_args__ = (
        UniqueConstraint("parlor_id", "name", name="uq_club_zones_parlor_name"),
        Index("ix_club_zones_parlor_active", "parlor_id", "is_active"),
    )

    parlor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("gaming_places.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ClubResource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One individually addressable bookable unit: a seat, PC, PS5, pool table, VR rig.

    This is the per-unit identity that `ParlorStation` (aggregate `total_count` per
    station type) does not provide. `ClubResource.resource_type` intentionally mirrors
    `ParlorStation.station_type` semantics so availability can reconcile the two:
    see `club_ops.service.ResourceService.station_type_for`.
    """

    __tablename__ = "club_resources"
    __table_args__ = (
        UniqueConstraint("parlor_id", "label", name="uq_club_resources_parlor_label"),
        CheckConstraint(
            f"resource_type IN ({_values(ResourceType)})", name="ck_club_resources_type"
        ),
        CheckConstraint(
            f"status IN ({_values(ResourceStatus)})", name="ck_club_resources_status"
        ),
        CheckConstraint(
            "hourly_rate_override_paise IS NULL OR hourly_rate_override_paise >= 0",
            name="ck_club_resources_rate",
        ),
        Index("ix_club_resources_parlor_type", "parlor_id", "resource_type", "is_active"),
        Index("ix_club_resources_parlor_status", "parlor_id", "status"),
    )

    parlor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("gaming_places.id", ondelete="CASCADE"), nullable=False, index=True
    )
    zone_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("club_zones.id", ondelete="SET NULL"), nullable=True, index=True
    )
    resource_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ResourceType.PC.value
    )
    label: Mapped[str] = mapped_column(String(60), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ResourceStatus.AVAILABLE.value
    )
    #: Free-form hardware/spec detail (GPU, monitor Hz, controller count...).
    specs: Mapped[dict | None] = mapped_column(PortableJSON, nullable=True)
    #: Per-unit rate override in paise. NULL means "fall through to pricing rules".
    hourly_rate_override_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    #: Floor-map coordinates, arbitrary units resolved by the client's canvas.
    layout_x: Mapped[int | None] = mapped_column(Integer, nullable=True)
    layout_y: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ClubPricingRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A resolvable price rule for a club.

    Resolution order is (scope specificity, then `priority` desc, then newest):
    resource > zone > resource_type > club. See `club_ops.pricing.PriceResolver`,
    which is the single price authority both booking paths call.

    JSON shapes (validated by the Pydantic schemas, stored loosely):
      time_slabs: [{"label": "peak", "start": "18:00", "end": "23:00",
                    "multiplier_bps": 15000}]           # or {"flat_paise": 15000}
      day_of_week_overrides: {"5": {"multiplier_bps": 12000}}   # 0=Mon .. 6=Sun
      package_defs: [{"label": "3hr bundle", "hours": 3, "price_paise": 25000}]
    """

    __tablename__ = "club_pricing_rules"
    __table_args__ = (
        CheckConstraint(
            f"scope IN ({_values(PricingScope)})", name="ck_club_pricing_rules_scope"
        ),
        CheckConstraint("base_rate_paise >= 0", name="ck_club_pricing_rules_base_rate"),
        Index("ix_club_pricing_rules_lookup", "parlor_id", "is_active", "scope"),
    )

    parlor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("gaming_places.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    scope: Mapped[str] = mapped_column(
        String(20), nullable=False, default=PricingScope.CLUB.value
    )
    #: Meaning depends on `scope`: a ResourceType value, a zone UUID, a resource UUID,
    #: or "" for club-wide. Kept as text so one column serves every scope.
    scope_value: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    base_rate_paise: Mapped[int] = mapped_column(Integer, nullable=False)
    time_slabs: Mapped[list | None] = mapped_column(PortableJSON, nullable=True)
    day_of_week_overrides: Mapped[dict | None] = mapped_column(PortableJSON, nullable=True)
    package_defs: Mapped[list | None] = mapped_column(PortableJSON, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ClubPromotion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A club-scoped discount.

    Deliberately separate from the existing platform-side `ParlourOffer` (which stays
    the customer-app offer surface); this is the owner-managed promotion set. Both are
    applied through `club_ops.promotions.PromotionService.apply_best` so a booking can
    never be double-discounted by the two mechanisms.

    Value is split into two integer columns rather than one polymorphic `value` so
    money stays in paise and percentages stay exact:
      percent -> `percent_bps` (basis points; 1000 = 10%)
      flat    -> `flat_paise`
    """

    __tablename__ = "club_promotions"
    __table_args__ = (
        UniqueConstraint("parlor_id", "code", name="uq_club_promotions_parlor_code"),
        CheckConstraint(
            f"promo_type IN ({_values(PromotionType)})", name="ck_club_promotions_type"
        ),
        CheckConstraint(
            "percent_bps IS NULL OR (percent_bps > 0 AND percent_bps <= 10000)",
            name="ck_club_promotions_percent",
        ),
        CheckConstraint(
            "flat_paise IS NULL OR flat_paise > 0", name="ck_club_promotions_flat"
        ),
        CheckConstraint(
            "percent_bps IS NOT NULL OR flat_paise IS NOT NULL",
            name="ck_club_promotions_has_value",
        ),
        CheckConstraint("used_count >= 0", name="ck_club_promotions_used_count"),
        Index("ix_club_promotions_active", "parlor_id", "is_active", "valid_to"),
    )

    parlor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("gaming_places.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    promo_type: Mapped[str] = mapped_column(String(20), nullable=False)
    percent_bps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    flat_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    #: Optional customer-entered code. Unique per club when present.
    code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    #: Ceiling on a percent discount so "50% off" can't blow up a long session.
    max_discount_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_amount_paise: Mapped[int | None] = mapped_column(Integer, nullable=True)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    #: happy_hour window, IST wall-clock. Both NULL for non-happy-hour promos.
    happy_hour_start: Mapped[time | None] = mapped_column(Time, nullable=True)
    happy_hour_end: Mapped[time | None] = mapped_column(Time, nullable=True)
    usage_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    #: List of ResourceType values this applies to; NULL/empty means all types.
    applicable_resource_types: Mapped[list | None] = mapped_column(PortableJSON, nullable=True)
    #: Minimum loyalty points for `loyalty` promos.
    min_loyalty_points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    #: Platform-admin override kill switch — an owner cannot clear this.
    disabled_by_platform: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    disabled_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class ClubCustomer(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A club's relationship with a customer. Does NOT duplicate `User`.

    `user_id` is nullable so walk-in customers who have no app account can still be
    tracked (identified by `phone`/`display_name`). The unique constraint on
    (parlor_id, user_id) permits many NULL rows, since NULLs compare distinct — walk-ins
    are de-duplicated on `phone` at the service layer instead.
    """

    __tablename__ = "club_customers"
    __table_args__ = (
        UniqueConstraint("parlor_id", "user_id", name="uq_club_customers_parlor_user"),
        CheckConstraint("visit_count >= 0", name="ck_club_customers_visit_count"),
        CheckConstraint("total_spend_paise >= 0", name="ck_club_customers_spend"),
        Index("ix_club_customers_parlor_last_visit", "parlor_id", "last_visit_at"),
        Index("ix_club_customers_parlor_phone", "parlor_id", "phone"),
    )

    parlor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("gaming_places.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    #: Denormalised for walk-ins with no linked user; for linked users the User row wins.
    display_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    visit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_spend_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_visit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    loyalty_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tags: Mapped[list | None] = mapped_column(PortableJSON, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ban_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    banned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    #: Platform-level flag set by an admin; the owner cannot clear it.
    platform_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    platform_flag_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class ClubCustomerNote(Base, UUIDPrimaryKeyMixin):
    """Append-only note timeline for a club customer (the `notes` text column is the
    current summary; this is the history, so notes from different staff aren't lost)."""

    __tablename__ = "club_customer_notes"
    __table_args__ = (Index("ix_club_customer_notes_customer", "club_customer_id", "created_at"),)

    club_customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("club_customers.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )


class OccupancyRollup(Base, UUIDPrimaryKeyMixin):
    """Precomputed hourly occupancy/revenue bucket. Written by Celery, read by analytics.

    One row per (parlor, hour bucket, grain, grain_key). `bucket_start` is stored as an
    aware UTC timestamp but always lands on an IST hour boundary, because the business
    day, peak-hour windows and day-of-week rollups are all Asia/Kolkata (see
    `club_ops.analytics_service.IST`).

    Idempotency: the unique constraint below is what makes the rollup task safe to
    re-run for a bucket — the task upserts on it rather than inserting blindly.
    """

    __tablename__ = "club_occupancy_rollups"
    __table_args__ = (
        UniqueConstraint(
            "parlor_id", "bucket_start", "grain", "grain_key", name="uq_club_rollup_bucket"
        ),
        CheckConstraint(f"grain IN ({_values(RollupGrain)})", name="ck_club_rollup_grain"),
        CheckConstraint("occupied_minutes >= 0", name="ck_club_rollup_occupied"),
        CheckConstraint("capacity_minutes >= 0", name="ck_club_rollup_capacity"),
        Index("ix_club_rollup_range", "parlor_id", "grain", "bucket_start"),
    )

    parlor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("gaming_places.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    grain: Mapped[str] = mapped_column(String(20), nullable=False)
    #: "" for club grain, a ResourceType value, or a zone/resource UUID as text.
    grain_key: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    #: IST-local hour (0-23) and weekday (0=Mon) denormalised for cheap heatmap queries.
    ist_hour: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    ist_weekday: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)
    occupied_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    capacity_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    booking_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    no_show_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revenue_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    commission_paise: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC)
    )
