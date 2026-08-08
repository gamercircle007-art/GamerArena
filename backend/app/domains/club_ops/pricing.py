"""The single price authority for a club booking.

Discovery found two independent booking paths computing price separately — the legacy
`SlotEngine`/`GamingBookingService` flow and the newer `AvailabilityService.create_booking_v2`
flow — both flat-rate, neither aware of the other. This resolver exists so both call one
function, and so `POST /club/pricing/preview` can never diverge from what a booking is
actually charged: the preview endpoint and the booking path invoke the *same* method.

All money is integer paise. All wall-clock reasoning is Asia/Kolkata, because peak
windows and day-of-week overrides are business rules expressed in local time.

Rate precedence, most specific first:
  1. `ClubResource.hourly_rate_override_paise`  (this exact unit is priced by hand)
  2. `ClubPricingRule` with scope resource > zone > resource_type > club
     (ties broken by `priority` desc, then most recently created)
  3. `ParlorStation.hourly_price_paise`         (the existing station-type rate)
  4. `GamingPlaceExtension.price_per_hour`      (the existing venue rate, rupees)
  5. `DEFAULT_RATE_PAISE`                       (mirrors SlotEngine.DEFAULT_PRICE)

On top of the resolved base rate, per booked hour:
  - the matching `time_slabs` entry (peak / off-peak) applies a `multiplier_bps`
    (10000 = 1.0x) or replaces the hour outright with `flat_paise`
  - `day_of_week_overrides[weekday]` then applies its own multiplier/flat
A `package_defs` entry whose `hours` equals the requested duration short-circuits the
hourly maths entirely — that is the point of selling a bundle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as date_cls
from datetime import datetime, time, timedelta
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.club_ops.enums import PricingScope, ResourceType
from app.domains.club_ops.models import ClubPricingRule, ClubResource
from app.domains.gaming_booking.inventory_models import ParlorStation
from app.domains.gaming_place.models import GamingPlaceExtension

IST = ZoneInfo("Asia/Kolkata")

#: Mirrors SlotEngine.DEFAULT_PRICE (Decimal("99.00")) so an unconfigured club prices
#: identically through either path.
DEFAULT_RATE_PAISE = 9900

BPS_ONE = 10000

#: How specific each scope is; higher wins.
_SCOPE_RANK = {
    PricingScope.CLUB.value: 0,
    PricingScope.RESOURCE_TYPE.value: 1,
    PricingScope.ZONE.value: 2,
    PricingScope.RESOURCE.value: 3,
}

#: ClubResource.resource_type <-> ParlorStation.station_type. The station table predates
#: typed resources and uses upper-case short codes; this keeps the two reconcilable
#: instead of letting them drift.
RESOURCE_TYPE_TO_STATION = {
    ResourceType.PC.value: "PC",
    ResourceType.PS5.value: "PS5",
    ResourceType.CONSOLE.value: "XBOX",
    ResourceType.VR.value: "VR",
    ResourceType.POOL.value: "POOL",
    ResourceType.SEAT.value: "PC",
    ResourceType.OTHER.value: "PC",
}
STATION_TO_RESOURCE_TYPE = {
    "PC": ResourceType.PC.value,
    "PS5": ResourceType.PS5.value,
    "XBOX": ResourceType.CONSOLE.value,
    "CONSOLE": ResourceType.CONSOLE.value,
    "VR": ResourceType.VR.value,
    "POOL": ResourceType.POOL.value,
}


def station_type_for(resource_type: str) -> str:
    return RESOURCE_TYPE_TO_STATION.get(resource_type, "PC")


def resource_type_for(station_type: str | None) -> str:
    if not station_type:
        return ResourceType.PC.value
    return STATION_TO_RESOURCE_TYPE.get(station_type.upper(), ResourceType.OTHER.value)


def _parse_hhmm(value: str | None) -> time | None:
    if not value:
        return None
    parts = str(value).split(":")
    try:
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
    except (TypeError, ValueError):
        return None
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return time(hour, minute)


def _in_window(moment: time, start: time, end: time) -> bool:
    """Window membership, honouring windows that wrap past midnight (22:00 -> 02:00)."""
    if start == end:
        return True
    if start < end:
        return start <= moment < end
    return moment >= start or moment < end


@dataclass
class HourPrice:
    """One booked hour's price and why it came out that way."""

    start_time: str
    rate_paise: int
    slab_label: str | None = None
    dow_override: bool = False


@dataclass
class PriceBreakdown:
    """The resolved price plus a full audit trail of how it was reached.

    The Flutter/Angular pricing screens render this directly, which is what makes a
    surprising price debuggable by the owner rather than a mystery.
    """

    subtotal_paise: int
    base_rate_paise: int
    hours: int
    units: int
    source: str
    rule_id: UUID | None = None
    rule_name: str | None = None
    package_label: str | None = None
    per_hour: list[HourPrice] = field(default_factory=list)

    @property
    def subtotal_rupees(self) -> str:
        return f"{Decimal(self.subtotal_paise) / 100:.2f}"

    def as_dict(self) -> dict:
        return {
            "subtotal_paise": self.subtotal_paise,
            "subtotal_rupees": self.subtotal_rupees,
            "base_rate_paise": self.base_rate_paise,
            "hours": self.hours,
            "units": self.units,
            "source": self.source,
            "rule_id": str(self.rule_id) if self.rule_id else None,
            "rule_name": self.rule_name,
            "package_label": self.package_label,
            "per_hour": [
                {
                    "start_time": h.start_time,
                    "rate_paise": h.rate_paise,
                    "slab_label": h.slab_label,
                    "dow_override": h.dow_override,
                }
                for h in self.per_hour
            ],
        }


class PriceResolver:
    """Resolves the price of a club booking. The only place that decides a rate."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def resolve(
        self,
        *,
        parlor_id: UUID,
        resource_type: str,
        booking_date: date_cls,
        start_time: time,
        duration_hours: int,
        units: int = 1,
        resource_id: UUID | None = None,
        zone_id: UUID | None = None,
    ) -> PriceBreakdown:
        if duration_hours < 1:
            raise ValueError("duration_hours must be >= 1")
        if units < 1:
            raise ValueError("units must be >= 1")

        resource: ClubResource | None = None
        if resource_id is not None:
            resource = (
                await self.session.execute(
                    select(ClubResource).where(
                        ClubResource.id == resource_id,
                        # Scoping still applies inside the resolver — a resource id from
                        # another club must not be able to drag its rate across.
                        ClubResource.parlor_id == parlor_id,
                    )
                )
            ).scalar_one_or_none()
            if resource is not None:
                resource_type = resource.resource_type
                if zone_id is None:
                    zone_id = resource.zone_id

        rule = await self._best_rule(
            parlor_id=parlor_id,
            resource_type=resource_type,
            resource_id=resource.id if resource else resource_id,
            zone_id=zone_id,
            at=datetime.combine(booking_date, start_time, tzinfo=IST),
        )

        # A per-unit override beats every rule's base rate, but still lets the rule's
        # slabs/day-of-week shape apply on top of it.
        if resource is not None and resource.hourly_rate_override_paise is not None:
            base_rate = resource.hourly_rate_override_paise
            source = "resource_override"
        elif rule is not None:
            base_rate = rule.base_rate_paise
            source = "pricing_rule"
        else:
            base_rate, source = await self._fallback_rate(parlor_id, resource_type)

        # A package for this exact duration replaces the hourly computation.
        if rule is not None:
            package = self._match_package(rule, duration_hours)
            if package is not None:
                total = int(package["price_paise"]) * units
                return PriceBreakdown(
                    subtotal_paise=total,
                    base_rate_paise=base_rate,
                    hours=duration_hours,
                    units=units,
                    source="package",
                    rule_id=rule.id,
                    rule_name=rule.name,
                    package_label=package.get("label"),
                )

        per_hour: list[HourPrice] = []
        running = 0
        for offset in range(duration_hours):
            hour_start = (
                datetime.combine(booking_date, start_time) + timedelta(hours=offset)
            )
            rate, slab_label, dow = self._rate_for_hour(rule, base_rate, hour_start)
            running += rate
            per_hour.append(
                HourPrice(
                    start_time=hour_start.time().strftime("%H:%M"),
                    rate_paise=rate,
                    slab_label=slab_label,
                    dow_override=dow,
                )
            )

        return PriceBreakdown(
            subtotal_paise=running * units,
            base_rate_paise=base_rate,
            hours=duration_hours,
            units=units,
            source=source,
            rule_id=rule.id if rule else None,
            rule_name=rule.name if rule else None,
            per_hour=per_hour,
        )

    # ---- internals -------------------------------------------------------------

    async def _best_rule(
        self,
        *,
        parlor_id: UUID,
        resource_type: str,
        resource_id: UUID | None,
        zone_id: UUID | None,
        at: datetime,
    ) -> ClubPricingRule | None:
        """Most specific active rule that covers this booking, or None."""
        rows = (
            await self.session.execute(
                select(ClubPricingRule).where(
                    ClubPricingRule.parlor_id == parlor_id,
                    ClubPricingRule.is_active.is_(True),
                )
            )
        ).scalars().all()

        candidates: list[ClubPricingRule] = []
        for rule in rows:
            if not self._rule_in_effect(rule, at):
                continue
            if rule.scope == PricingScope.CLUB.value:
                candidates.append(rule)
            elif rule.scope == PricingScope.RESOURCE_TYPE.value:
                if rule.scope_value == resource_type:
                    candidates.append(rule)
            elif rule.scope == PricingScope.ZONE.value:
                if zone_id is not None and rule.scope_value == str(zone_id):
                    candidates.append(rule)
            elif rule.scope == PricingScope.RESOURCE.value:
                if resource_id is not None and rule.scope_value == str(resource_id):
                    candidates.append(rule)

        if not candidates:
            return None
        candidates.sort(
            key=lambda r: (
                _SCOPE_RANK.get(r.scope, 0),
                r.priority,
                r.created_at or datetime.min.replace(tzinfo=IST),
            ),
            reverse=True,
        )
        return candidates[0]

    @staticmethod
    def _rule_in_effect(rule: ClubPricingRule, at: datetime) -> bool:
        if rule.valid_from is not None:
            valid_from = rule.valid_from
            if valid_from.tzinfo is None:
                valid_from = valid_from.replace(tzinfo=IST)
            if at < valid_from:
                return False
        if rule.valid_to is not None:
            valid_to = rule.valid_to
            if valid_to.tzinfo is None:
                valid_to = valid_to.replace(tzinfo=IST)
            if at > valid_to:
                return False
        return True

    @staticmethod
    def _match_package(rule: ClubPricingRule, duration_hours: int) -> dict | None:
        for package in rule.package_defs or []:
            if not isinstance(package, dict):
                continue
            try:
                if int(package.get("hours", -1)) == duration_hours:
                    if int(package.get("price_paise", -1)) >= 0:
                        return package
            except (TypeError, ValueError):
                continue
        return None

    def _rate_for_hour(
        self, rule: ClubPricingRule | None, base_rate: int, hour_start: datetime
    ) -> tuple[int, str | None, bool]:
        """Apply the time slab, then the day-of-week override, to one hour."""
        rate = base_rate
        slab_label: str | None = None
        dow_applied = False
        if rule is None:
            return rate, slab_label, dow_applied

        moment = hour_start.time()
        for slab in rule.time_slabs or []:
            if not isinstance(slab, dict):
                continue
            start = _parse_hhmm(slab.get("start"))
            end = _parse_hhmm(slab.get("end"))
            if start is None or end is None or not _in_window(moment, start, end):
                continue
            rate = self._apply_modifier(rate, slab)
            slab_label = slab.get("label") or "slab"
            break

        overrides = rule.day_of_week_overrides or {}
        if isinstance(overrides, dict):
            # Keys arrive as JSON strings ("5"); accept ints too for tolerance.
            override = overrides.get(str(hour_start.weekday()), overrides.get(hour_start.weekday()))
            if isinstance(override, dict):
                rate = self._apply_modifier(rate, override)
                dow_applied = True

        return max(0, rate), slab_label, dow_applied

    @staticmethod
    def _apply_modifier(rate: int, spec: dict) -> int:
        """`flat_paise` replaces the hour; `multiplier_bps` scales it (10000 = 1.0x)."""
        flat = spec.get("flat_paise")
        if flat is not None:
            try:
                return max(0, int(flat))
            except (TypeError, ValueError):
                return rate
        multiplier = spec.get("multiplier_bps")
        if multiplier is not None:
            try:
                return max(0, (rate * int(multiplier)) // BPS_ONE)
            except (TypeError, ValueError):
                return rate
        return rate

    async def _fallback_rate(self, parlor_id: UUID, resource_type: str) -> tuple[int, str]:
        """No pricing rule configured — reuse the rates the app already books at."""
        station = (
            await self.session.execute(
                select(ParlorStation).where(
                    ParlorStation.parlor_id == parlor_id,
                    ParlorStation.station_type == station_type_for(resource_type),
                    ParlorStation.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if station is not None and station.hourly_price_paise:
            return station.hourly_price_paise, "station"

        ext = (
            await self.session.execute(
                select(GamingPlaceExtension).where(
                    GamingPlaceExtension.gaming_place_id == parlor_id
                )
            )
        ).scalar_one_or_none()
        if ext is not None and ext.price_per_hour:
            try:
                paise = int(Decimal(str(ext.price_per_hour)) * 100)
                if paise > 0:
                    return paise, "venue"
            except (TypeError, ValueError, ArithmeticError):
                pass

        return DEFAULT_RATE_PAISE, "default"
