"""Club-ops enumerations.

Stored as short strings (with DB CHECK constraints) rather than native PostgreSQL
enum types, matching the existing convention in this codebase (`ParlorStation.station_type`
is a `String(20)`) and keeping the models usable on the SQLite dev database that
`scripts/run_dev.py` builds via `metadata.create_all`. Adding a new member therefore
only needs a CHECK-constraint migration, not an ALTER TYPE.
"""

from __future__ import annotations

from enum import Enum


class ResourceType(str, Enum):
    """The generic bookable unit. One typed model, not one model per kind."""

    SEAT = "seat"
    PC = "pc"
    CONSOLE = "console"
    PS5 = "ps5"
    POOL = "pool"
    VR = "vr"
    OTHER = "other"


class ResourceStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class PricingScope(str, Enum):
    """What a pricing rule attaches to, most general to most specific."""

    CLUB = "club"
    RESOURCE_TYPE = "resource_type"
    ZONE = "zone"
    RESOURCE = "resource"


class PromotionType(str, Enum):
    PERCENT = "percent"
    FLAT = "flat"
    HAPPY_HOUR = "happy_hour"
    FIRST_VISIT = "first_visit"
    LOYALTY = "loyalty"
    CODE = "code"


class RollupGrain(str, Enum):
    """Discriminator for an OccupancyRollup row's aggregation level.

    Kept explicit (rather than nullable resource_id/zone_id columns) so the
    idempotency unique key (parlor_id, bucket_start, grain, grain_key) never
    involves NULLs — NULLs compare as distinct and would let the Celery job
    insert duplicate buckets on a re-run.
    """

    CLUB = "club"
    RESOURCE_TYPE = "resource_type"
    ZONE = "zone"
    RESOURCE = "resource"


# Booking lifecycle statuses this domain adds on top of the existing
# confirmed / payment_pending / initiated / cancelled / expired / refund_pending set.
BOOKING_STATUS_CHECKED_IN = "checked_in"
BOOKING_STATUS_COMPLETED = "completed"
BOOKING_STATUS_NO_SHOW = "no_show"

#: Statuses that occupy inventory for availability/occupancy purposes.
OCCUPYING_STATUSES: tuple[str, ...] = (
    "confirmed",
    "payment_pending",
    "initiated",
    BOOKING_STATUS_CHECKED_IN,
)

#: Statuses that count as a delivered, revenue-bearing session.
COMPLETED_STATUSES: tuple[str, ...] = (
    "confirmed",
    BOOKING_STATUS_CHECKED_IN,
    BOOKING_STATUS_COMPLETED,
)
