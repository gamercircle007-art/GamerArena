"""Club Management services: zones, resources, owner booking ops, customer CRM.

Every public method takes an already-resolved `parlor_id` (see
`club_ops.repository.ClubScope`) and filters on it. Nothing here re-derives the club
from a request — that resolution happens once, in the router, before any of this runs.

Booking operations extend the existing `gaming_bookings` table rather than forking a
second booking model: a walk-in is a `GamingBooking` with `is_walk_in=True`, and
check-in/out/extend/no-show move the same `booking_status` column the customer app
already reads. Every transition writes a `BookingAudit` row, matching the audit trail
`AvailabilityService` already keeps.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date as date_cls, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.club_ops.enums import (
    BOOKING_STATUS_CHECKED_IN,
    BOOKING_STATUS_COMPLETED,
    BOOKING_STATUS_NO_SHOW,
    OCCUPYING_STATUSES,
    ResourceStatus,
)
from app.domains.club_ops.models import (
    ClubCustomer,
    ClubCustomerNote,
    ClubPricingRule,
    ClubResource,
    ClubZone,
)
from app.domains.club_ops.pricing import PriceResolver, resource_type_for, station_type_for
from app.domains.club_ops.promotions import PromotionService
from app.domains.common.exceptions import ConflictError, NotFoundError, ValidationError
from app.domains.gaming_booking.booking_ref import generate_booking_ref
from app.domains.gaming_booking.inventory_models import BookingAudit, BookingUnitLock
from app.domains.gaming_booking.lock_service import _is_exclusion_violation, build_during
from app.domains.gaming_booking.models import GamingBooking
from app.domains.user.models import User

IST = ZoneInfo("Asia/Kolkata")


def today_ist() -> date_cls:
    return datetime.now(IST).date()


def _paise_to_decimal(paise: int) -> Decimal:
    return (Decimal(paise) / Decimal(100)).quantize(Decimal("0.01"))


class ZoneService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_zones(self, parlor_id: UUID) -> list[tuple[ClubZone, int]]:
        """Zones plus their resource counts, ordered for display."""
        counts = dict(
            (
                await self.session.execute(
                    select(ClubResource.zone_id, func.count(ClubResource.id))
                    .where(ClubResource.parlor_id == parlor_id)
                    .group_by(ClubResource.zone_id)
                )
            ).all()
        )
        zones = (
            await self.session.execute(
                select(ClubZone)
                .where(ClubZone.parlor_id == parlor_id)
                .order_by(ClubZone.sort_order.asc(), ClubZone.name.asc())
            )
        ).scalars().all()
        return [(z, int(counts.get(z.id, 0))) for z in zones]

    async def get(self, parlor_id: UUID, zone_id: UUID) -> ClubZone:
        zone = (
            await self.session.execute(
                select(ClubZone).where(ClubZone.id == zone_id, ClubZone.parlor_id == parlor_id)
            )
        ).scalar_one_or_none()
        if zone is None:
            raise NotFoundError("Zone not found")
        return zone

    async def create(self, parlor_id: UUID, data) -> ClubZone:
        zone = ClubZone(
            parlor_id=parlor_id,
            name=data.name.strip(),
            description=data.description,
            sort_order=data.sort_order,
            is_active=True,
        )
        self.session.add(zone)
        await self.session.commit()
        await self.session.refresh(zone)
        return zone

    async def update(self, parlor_id: UUID, zone_id: UUID, data) -> ClubZone:
        zone = await self.get(parlor_id, zone_id)
        for field in ("name", "description", "sort_order", "is_active"):
            value = getattr(data, field, None)
            if value is not None:
                setattr(zone, field, value.strip() if field == "name" else value)
        await self.session.commit()
        await self.session.refresh(zone)
        return zone

    async def delete(self, parlor_id: UUID, zone_id: UUID) -> None:
        """Soft delete: resources keep working, they just lose their grouping."""
        zone = await self.get(parlor_id, zone_id)
        zone.is_active = False
        await self.session.commit()


class ResourceService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_resources(
        self,
        parlor_id: UUID,
        *,
        zone_id: UUID | None = None,
        resource_type: str | None = None,
        status: str | None = None,
        include_inactive: bool = False,
    ) -> list[tuple[ClubResource, str | None]]:
        stmt = select(ClubResource, ClubZone.name).outerjoin(
            ClubZone, ClubResource.zone_id == ClubZone.id
        ).where(ClubResource.parlor_id == parlor_id)
        if zone_id is not None:
            stmt = stmt.where(ClubResource.zone_id == zone_id)
        if resource_type:
            stmt = stmt.where(ClubResource.resource_type == resource_type)
        if status:
            stmt = stmt.where(ClubResource.status == status)
        if not include_inactive:
            stmt = stmt.where(ClubResource.is_active.is_(True))
        rows = (
            await self.session.execute(
                stmt.order_by(ClubZone.sort_order.asc().nullslast(), ClubResource.label.asc())
            )
        ).all()
        return [(row[0], row[1]) for row in rows]

    async def get(self, parlor_id: UUID, resource_id: UUID) -> ClubResource:
        resource = (
            await self.session.execute(
                select(ClubResource).where(
                    ClubResource.id == resource_id, ClubResource.parlor_id == parlor_id
                )
            )
        ).scalar_one_or_none()
        if resource is None:
            raise NotFoundError("Resource not found")
        return resource

    async def create(self, parlor_id: UUID, data) -> ClubResource:
        if data.zone_id is not None:
            await ZoneService(self.session).get(parlor_id, data.zone_id)
        resource = ClubResource(
            parlor_id=parlor_id,
            zone_id=data.zone_id,
            resource_type=data.resource_type.value,
            label=data.label.strip(),
            status=data.status.value,
            specs=data.specs,
            hourly_rate_override_paise=data.hourly_rate_override_paise,
            layout_x=data.layout_x,
            layout_y=data.layout_y,
            is_active=data.is_active,
        )
        self.session.add(resource)
        await self.session.commit()
        await self.session.refresh(resource)
        return resource

    async def update(self, parlor_id: UUID, resource_id: UUID, data) -> ClubResource:
        resource = await self.get(parlor_id, resource_id)
        if data.zone_id is not None:
            await ZoneService(self.session).get(parlor_id, data.zone_id)
            resource.zone_id = data.zone_id
        if data.label is not None:
            resource.label = data.label.strip()
        if data.resource_type is not None:
            resource.resource_type = data.resource_type.value
        if data.status is not None:
            resource.status = data.status.value
        for field in (
            "specs",
            "hourly_rate_override_paise",
            "layout_x",
            "layout_y",
            "status_note",
            "is_active",
        ):
            value = getattr(data, field, None)
            if value is not None:
                setattr(resource, field, value)
        await self.session.commit()
        await self.session.refresh(resource)
        return resource

    async def delete(self, parlor_id: UUID, resource_id: UUID) -> None:
        """Deactivate rather than delete — historical bookings reference this row."""
        resource = await self.get(parlor_id, resource_id)
        resource.is_active = False
        resource.status = ResourceStatus.OFFLINE.value
        await self.session.commit()

    async def set_status(
        self, parlor_id: UUID, resource_id: UUID, status: str, note: str | None = None
    ) -> ClubResource:
        resource = await self.get(parlor_id, resource_id)
        resource.status = status
        resource.status_note = note
        await self.session.commit()
        await self.session.refresh(resource)
        return resource

    async def bulk_set_status(
        self, parlor_id: UUID, resource_ids: list[UUID], status: str, note: str | None = None
    ) -> int:
        """Bulk status change, scoped — ids from another club are silently not matched
        (rather than 403) so one stray id cannot fail the whole floor update."""
        rows = (
            await self.session.execute(
                select(ClubResource).where(
                    ClubResource.parlor_id == parlor_id,
                    ClubResource.id.in_(resource_ids),
                )
            )
        ).scalars().all()
        for resource in rows:
            resource.status = status
            resource.status_note = note
        await self.session.commit()
        return len(rows)

    async def save_layout(self, parlor_id: UUID, positions) -> int:
        by_id = {p.resource_id: p for p in positions}
        rows = (
            await self.session.execute(
                select(ClubResource).where(
                    ClubResource.parlor_id == parlor_id,
                    ClubResource.id.in_(list(by_id.keys())),
                )
            )
        ).scalars().all()
        for resource in rows:
            position = by_id[resource.id]
            resource.layout_x = position.layout_x
            resource.layout_y = position.layout_y
        await self.session.commit()
        return len(rows)

    async def pick_free_resource(
        self,
        parlor_id: UUID,
        resource_type: str,
        booking_date: date_cls,
        start_time: time,
        duration_hours: int,
    ) -> ClubResource | None:
        """First active resource of this type with no overlapping booking.

        Used by the walk-in flow so counter staff don't have to choose a seat manually.
        Returns None when the club has no `ClubResource` rows at all, in which case the
        booking is still created (capacity then falls back to `ParlorStation`, exactly
        as the existing availability path does).
        """
        candidates = (
            await self.session.execute(
                select(ClubResource)
                .where(
                    ClubResource.parlor_id == parlor_id,
                    ClubResource.resource_type == resource_type,
                    ClubResource.is_active.is_(True),
                    ClubResource.status.in_(
                        (ResourceStatus.AVAILABLE.value, ResourceStatus.RESERVED.value)
                    ),
                )
                .order_by(ClubResource.label.asc())
            )
        ).scalars().all()
        if not candidates:
            return None

        busy = await self._busy_resource_ids(
            parlor_id, booking_date, start_time, duration_hours
        )
        for resource in candidates:
            if resource.id not in busy:
                return resource
        return None

    async def _busy_resource_ids(
        self, parlor_id: UUID, booking_date: date_cls, start_time: time, duration_hours: int
    ) -> set[UUID]:
        end_minutes = _minutes(start_time) + duration_hours * 60
        start_minutes = _minutes(start_time)
        rows = (
            await self.session.execute(
                select(GamingBooking).where(
                    GamingBooking.parlour_id == parlor_id,
                    GamingBooking.slot_date == booking_date,
                    GamingBooking.resource_id.is_not(None),
                    GamingBooking.booking_status.in_(OCCUPYING_STATUSES),
                )
            )
        ).scalars().all()
        busy: set[UUID] = set()
        for booking in rows:
            if booking.start_time is None:
                continue
            b_start = _minutes(booking.start_time)
            b_end = b_start + (int(booking.duration_hours or 1) + int(booking.extended_hours or 0)) * 60
            if b_start < end_minutes and start_minutes < b_end:
                busy.add(booking.resource_id)
        return busy


def _minutes(value: time) -> int:
    return value.hour * 60 + value.minute


class CustomerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_customers(
        self, parlor_id: UUID, *, search: str | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[ClubCustomer], int]:
        stmt = select(ClubCustomer).where(ClubCustomer.parlor_id == parlor_id)
        if search:
            needle = f"%{search.strip()}%"
            # Search the club-local name/phone, and the linked User's name/phone.
            stmt = stmt.outerjoin(User, ClubCustomer.user_id == User.id).where(
                or_(
                    ClubCustomer.display_name.ilike(needle),
                    ClubCustomer.phone.ilike(needle),
                    User.full_name.ilike(needle),
                    User.username.ilike(needle),
                    User.phone.ilike(needle),
                )
            )
        total = (
            await self.session.execute(
                select(func.count()).select_from(stmt.subquery())
            )
        ).scalar_one()
        rows = (
            await self.session.execute(
                stmt.order_by(ClubCustomer.last_visit_at.desc().nullslast())
                .limit(limit)
                .offset(offset)
            )
        ).scalars().all()
        return list(rows), int(total)

    async def get(self, parlor_id: UUID, customer_id: UUID) -> ClubCustomer:
        customer = (
            await self.session.execute(
                select(ClubCustomer).where(
                    ClubCustomer.id == customer_id, ClubCustomer.parlor_id == parlor_id
                )
            )
        ).scalar_one_or_none()
        if customer is None:
            raise NotFoundError("Customer not found")
        return customer

    async def resolve_name(self, customer: ClubCustomer) -> str | None:
        if customer.display_name:
            return customer.display_name
        if customer.user_id is None:
            return None
        user = (
            await self.session.execute(select(User).where(User.id == customer.user_id))
        ).scalar_one_or_none()
        if user is None:
            return None
        return user.full_name or user.username

    async def ensure_for_user(self, parlor_id: UUID, user_id: UUID) -> ClubCustomer:
        """Get-or-create the club's record for an app user."""
        existing = (
            await self.session.execute(
                select(ClubCustomer).where(
                    ClubCustomer.parlor_id == parlor_id, ClubCustomer.user_id == user_id
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing
        customer = ClubCustomer(parlor_id=parlor_id, user_id=user_id)
        self.session.add(customer)
        await self.session.flush()
        return customer

    async def ensure_walk_in(
        self, parlor_id: UUID, *, name: str | None, phone: str | None
    ) -> ClubCustomer:
        """Get-or-create a walk-in customer, de-duplicated on phone within the club.

        Walk-ins have no `user_id`, so the (parlor_id, user_id) unique constraint cannot
        do this for us — phone is the practical identity at a counter.
        """
        if phone:
            existing = (
                await self.session.execute(
                    select(ClubCustomer).where(
                        ClubCustomer.parlor_id == parlor_id,
                        ClubCustomer.phone == phone.strip(),
                    )
                )
            ).scalar_one_or_none()
            if existing is not None:
                if name and not existing.display_name:
                    existing.display_name = name.strip()
                return existing
        customer = ClubCustomer(
            parlor_id=parlor_id,
            user_id=None,
            display_name=name.strip() if name else None,
            phone=phone.strip() if phone else None,
        )
        self.session.add(customer)
        await self.session.flush()
        return customer

    async def add_note(
        self, parlor_id: UUID, customer_id: UUID, body: str, author_id: UUID | None
    ) -> ClubCustomerNote:
        customer = await self.get(parlor_id, customer_id)
        note = ClubCustomerNote(
            club_customer_id=customer.id, author_id=author_id, body=body.strip()
        )
        self.session.add(note)
        # Keep the summary column as the latest note so list views show something useful.
        customer.notes = body.strip()
        await self.session.commit()
        await self.session.refresh(note)
        return note

    async def list_notes(
        self, parlor_id: UUID, customer_id: UUID, limit: int = 50
    ) -> list[ClubCustomerNote]:
        customer = await self.get(parlor_id, customer_id)
        rows = (
            await self.session.execute(
                select(ClubCustomerNote)
                .where(ClubCustomerNote.club_customer_id == customer.id)
                .order_by(ClubCustomerNote.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return list(rows)

    async def set_tags(self, parlor_id: UUID, customer_id: UUID, tags: list[str]) -> ClubCustomer:
        customer = await self.get(parlor_id, customer_id)
        cleaned: list[str] = []
        for tag in tags:
            value = tag.strip()
            if value and value not in cleaned:
                cleaned.append(value)
        customer.tags = cleaned
        await self.session.commit()
        await self.session.refresh(customer)
        return customer

    async def set_ban(
        self, parlor_id: UUID, customer_id: UUID, *, banned: bool, reason: str | None
    ) -> ClubCustomer:
        customer = await self.get(parlor_id, customer_id)
        customer.is_banned = banned
        customer.ban_reason = reason if banned else None
        customer.banned_at = datetime.now(UTC) if banned else None
        await self.session.commit()
        await self.session.refresh(customer)
        return customer

    async def record_visit(self, customer: ClubCustomer, *, spend_paise: int) -> None:
        """Roll a completed session into the customer's aggregates.

        Called on check-out (not on booking creation) so the numbers reflect sessions
        actually delivered. Loyalty accrues at 1 point per ₹100 spent.
        """
        customer.visit_count += 1
        customer.total_spend_paise += max(0, spend_paise)
        customer.last_visit_at = datetime.now(UTC)
        customer.loyalty_points += max(0, spend_paise) // 10000
        await self.session.flush()


class OwnerBookingService:
    """Owner-side booking operations layered on the existing GamingBooking model."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.resources = ResourceService(session)
        self.customers = CustomerService(session)
        self.pricing = PriceResolver(session)
        self.promotions = PromotionService(session)

    async def list_bookings(
        self,
        parlor_id: UUID,
        *,
        target_date: date_cls | None = None,
        view: str = "day",
        status: str | None = None,
    ) -> list[GamingBooking]:
        anchor = target_date or today_ist()
        if view == "week":
            # Week starts Monday, matching IST weekday indexing used across the domain.
            start = anchor - timedelta(days=anchor.weekday())
            end = start + timedelta(days=6)
        else:
            start = end = anchor

        stmt = select(GamingBooking).where(
            GamingBooking.parlour_id == parlor_id,
            GamingBooking.slot_date >= start,
            GamingBooking.slot_date <= end,
        )
        if status:
            stmt = stmt.where(GamingBooking.booking_status == status)
        rows = (
            await self.session.execute(
                stmt.order_by(GamingBooking.slot_date.asc(), GamingBooking.start_time.asc())
            )
        ).scalars().all()
        return list(rows)

    async def get(self, parlor_id: UUID, booking_id: UUID) -> GamingBooking:
        booking = (
            await self.session.execute(
                select(GamingBooking).where(
                    GamingBooking.id == booking_id,
                    # The scoping that stops an owner touching another club's booking.
                    GamingBooking.parlour_id == parlor_id,
                )
            )
        ).scalar_one_or_none()
        if booking is None:
            raise NotFoundError("Booking not found")
        return booking

    async def create_walk_in(
        self, parlor_id: UUID, data, *, actor_id: UUID | None
    ) -> GamingBooking:
        booking_date = data.booking_date or today_ist()
        start_time = data.start_time or datetime.now(IST).time().replace(
            minute=0, second=0, microsecond=0
        )
        resource_type = data.resource_type.value

        resource: ClubResource | None = None
        if data.resource_id is not None:
            resource = await self.resources.get(parlor_id, data.resource_id)
            resource_type = resource.resource_type
            if not resource.is_active:
                raise ValidationError("That resource is not active")
        else:
            resource = await self.resources.pick_free_resource(
                parlor_id, resource_type, booking_date, start_time, data.duration_hours
            )

        customer = await self.customers.ensure_walk_in(
            parlor_id, name=data.guest_name, phone=data.contact_phone
        )
        if customer.is_banned:
            raise ValidationError(
                f"This customer is banned from your club: {customer.ban_reason or 'no reason given'}"
            )

        breakdown = await self.pricing.resolve(
            parlor_id=parlor_id,
            resource_type=resource_type,
            booking_date=booking_date,
            start_time=start_time,
            duration_hours=data.duration_hours,
            units=data.units,
            resource_id=resource.id if resource else None,
            zone_id=resource.zone_id if resource else None,
        )
        promo = await self.promotions.apply_best(
            parlor_id=parlor_id,
            subtotal_paise=breakdown.subtotal_paise,
            resource_type=resource_type,
            booking_date=booking_date,
            start_time=start_time,
            code=data.promo_code,
            club_customer_id=customer.id,
        )
        if data.promo_code and not promo.valid:
            raise ValidationError(promo.reason or "Promotion is not valid")

        discount = promo.discount_paise if promo.valid else 0
        total_paise = max(0, breakdown.subtotal_paise - discount)
        end_time = (
            datetime.combine(booking_date, start_time) + timedelta(hours=data.duration_hours)
        ).time()

        now = datetime.now(UTC)
        checked_in = data.check_in_now
        during_start, during_end = build_during(
            booking_date, start_time, data.duration_hours
        )
        st = station_type_for(resource_type)
        booking = GamingBooking(
            booking_ref=await generate_booking_ref(self.session),
            # Walk-ins have no app account. `user_id` is NOT NULL on this legacy table,
            # so an unlinked walk-in is attributed to the acting staff member; the real
            # customer identity lives on club_customer_id.
            user_id=customer.user_id or actor_id,
            parlour_id=parlor_id,
            slot_id=None,
            guest_name=data.guest_name,
            num_players=data.units,
            slot_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            hours_booked=Decimal(data.duration_hours),
            price_per_hour=_paise_to_decimal(breakdown.base_rate_paise),
            total_price=_paise_to_decimal(breakdown.subtotal_paise),
            tax_amount=Decimal("0"),
            discount_amount=Decimal("0"),
            final_price=_paise_to_decimal(total_paise),
            payment_mode=data.payment_mode,
            payment_status="paid" if data.payment_mode == "cash" else "pending",
            booking_status=BOOKING_STATUS_CHECKED_IN if checked_in else "confirmed",
            contact_phone=data.contact_phone,
            station_type=st,
            duration_hours=data.duration_hours,
            units=data.units,
            amount_paise=total_paise,
            commission_paise=0,
            resource_id=resource.id if resource else None,
            club_customer_id=customer.id,
            club_promotion_id=promo.promotion_id if promo.valid else None,
            club_discount_paise=discount,
            is_walk_in=True,
            checked_in_at=now if checked_in else None,
            during_start=during_start,
            during_end=during_end,
            updated_at=now,
        )
        try:
            self.session.add(booking)
            await self.session.flush()

            # EXCLUDE is the correctness layer — same as customer holds (Step 8 / 38).
            for i in range(data.units):
                self.session.add(
                    BookingUnitLock(
                        booking_id=booking.id,
                        parlor_id=parlor_id,
                        station_type=st,
                        unit_index=i if resource is None else i,
                        resource_id=resource.id if resource is not None and i == 0 else None,
                        during_start=during_start,
                        during_end=during_end,
                        is_active=True,
                    )
                )
            await self.session.flush()
        except IntegrityError as exc:
            await self.session.rollback()
            if _is_exclusion_violation(exc):
                raise ConflictError(
                    "That seat was just taken — pick another",
                    details={"reason": "exclude_violation"},
                ) from exc
            raise

        if promo.valid and promo.promotion_id is not None:
            await self.promotions.consume(
                await self.promotions.get_scoped(parlor_id, promo.promotion_id)
            )
        if resource is not None and checked_in:
            resource.status = ResourceStatus.OCCUPIED.value

        self._audit(booking, None, booking.booking_status, actor_id, "walk_in_created")
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def confirm(self, parlor_id: UUID, booking_id: UUID, actor_id: UUID | None):
        booking = await self.get(parlor_id, booking_id)
        if booking.booking_status == "confirmed":
            return booking
        if booking.booking_status in ("cancelled", BOOKING_STATUS_NO_SHOW):
            raise ValidationError(f"Cannot confirm a {booking.booking_status} booking")
        old = booking.booking_status
        booking.booking_status = "confirmed"
        booking.updated_at = datetime.now(UTC)
        self._audit(booking, old, "confirmed", actor_id, "owner_confirm")
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def cancel(
        self, parlor_id: UUID, booking_id: UUID, *, reason: str, detail: str | None, actor_id: UUID | None, actor: str = "owner"
    ) -> GamingBooking:
        booking = await self.get(parlor_id, booking_id)
        if booking.booking_status == "cancelled":
            return booking
        if booking.checked_out_at is not None:
            raise ValidationError("Cannot cancel a completed session")

        old = booking.booking_status
        booking.booking_status = "cancelled"
        booking.cancellation_reason = reason
        booking.cancellation_detail = detail
        booking.cancelled_at = datetime.now(UTC)
        booking.cancelled_by = actor
        booking.updated_at = datetime.now(UTC)

        # Give the promotion use back, else a cancelled booking permanently burns a slot
        # of a limited-use promo.
        if booking.club_promotion_id is not None:
            promo = await self.promotions.get_scoped(parlor_id, booking.club_promotion_id)
            await self.promotions.release(promo)

        await self._free_resource(booking)
        self._audit(booking, old, "cancelled", actor_id, f"{actor}_cancel: {reason}")
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def check_in(self, parlor_id: UUID, booking_id: UUID, actor_id: UUID | None) -> GamingBooking:
        booking = await self.get(parlor_id, booking_id)
        if booking.checked_in_at is not None:
            return booking
        if booking.booking_status in ("cancelled", "expired", BOOKING_STATUS_NO_SHOW):
            raise ValidationError(f"Cannot check in a {booking.booking_status} booking")

        old = booking.booking_status
        booking.booking_status = BOOKING_STATUS_CHECKED_IN
        booking.checked_in_at = datetime.now(UTC)
        booking.updated_at = booking.checked_in_at
        if booking.resource_id is not None:
            resource = await self.resources.get(parlor_id, booking.resource_id)
            resource.status = ResourceStatus.OCCUPIED.value
        self._audit(booking, old, BOOKING_STATUS_CHECKED_IN, actor_id, "check_in")
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def check_out(self, parlor_id: UUID, booking_id: UUID, actor_id: UUID | None) -> GamingBooking:
        booking = await self.get(parlor_id, booking_id)
        if booking.checked_out_at is not None:
            return booking
        if booking.checked_in_at is None:
            raise ValidationError("Booking has not been checked in")

        old = booking.booking_status
        booking.booking_status = BOOKING_STATUS_COMPLETED
        booking.checked_out_at = datetime.now(UTC)
        booking.updated_at = booking.checked_out_at
        await self._free_resource(booking)

        # Customer aggregates update on check-out — the point at which the session is
        # actually delivered and its spend is final.
        if booking.club_customer_id is not None:
            customer = await self.customers.get(parlor_id, booking.club_customer_id)
            await self.customers.record_visit(
                customer, spend_paise=int(booking.amount_paise or 0)
            )
        self._audit(booking, old, BOOKING_STATUS_COMPLETED, actor_id, "check_out")
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def extend(
        self, parlor_id: UUID, booking_id: UUID, additional_hours: int, actor_id: UUID | None
    ) -> GamingBooking:
        booking = await self.get(parlor_id, booking_id)
        if booking.checked_out_at is not None:
            raise ValidationError("Session already checked out")
        if booking.booking_status in ("cancelled", BOOKING_STATUS_NO_SHOW):
            raise ValidationError(f"Cannot extend a {booking.booking_status} booking")
        if booking.slot_date is None or booking.start_time is None:
            raise ValidationError("Booking has no scheduled time to extend")

        already = int(booking.duration_hours or 1) + int(booking.extended_hours or 0)
        # Price only the added hours, through the same resolver, so an extension into
        # peak hours is charged at the peak rate.
        extra_start = (
            datetime.combine(booking.slot_date, booking.start_time)
            + timedelta(hours=already)
        )
        breakdown = await self.pricing.resolve(
            parlor_id=parlor_id,
            resource_type=resource_type_for(booking.station_type),
            booking_date=extra_start.date(),
            start_time=extra_start.time(),
            duration_hours=additional_hours,
            units=int(booking.units or 1),
            resource_id=booking.resource_id,
        )

        booking.extended_hours = int(booking.extended_hours or 0) + additional_hours
        booking.amount_paise = int(booking.amount_paise or 0) + breakdown.subtotal_paise
        booking.end_time = (
            datetime.combine(booking.slot_date, booking.start_time)
            + timedelta(hours=already + additional_hours)
        ).time()
        booking.hours_booked = Decimal(already + additional_hours)
        booking.final_price = _paise_to_decimal(int(booking.amount_paise))
        booking.updated_at = datetime.now(UTC)
        self._audit(
            booking,
            booking.booking_status,
            booking.booking_status,
            actor_id,
            f"extend_{additional_hours}h_+{breakdown.subtotal_paise}p",
        )
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def mark_no_show(
        self, parlor_id: UUID, booking_id: UUID, actor_id: UUID | None
    ) -> GamingBooking:
        booking = await self.get(parlor_id, booking_id)
        if booking.checked_in_at is not None:
            raise ValidationError("Customer already checked in")
        if booking.booking_status == BOOKING_STATUS_NO_SHOW:
            return booking

        old = booking.booking_status
        booking.booking_status = BOOKING_STATUS_NO_SHOW
        booking.no_show_at = datetime.now(UTC)
        booking.updated_at = booking.no_show_at
        await self._free_resource(booking)
        self._audit(booking, old, BOOKING_STATUS_NO_SHOW, actor_id, "no_show")
        await self.session.commit()
        await self.session.refresh(booking)
        return booking

    async def live_now(self, parlor_id: UUID) -> list[dict]:
        """Who is playing right now, driven by check-in/check-out."""
        rows = (
            await self.session.execute(
                select(GamingBooking, ClubResource)
                .outerjoin(ClubResource, GamingBooking.resource_id == ClubResource.id)
                .where(
                    GamingBooking.parlour_id == parlor_id,
                    GamingBooking.booking_status == BOOKING_STATUS_CHECKED_IN,
                    GamingBooking.checked_in_at.is_not(None),
                    GamingBooking.checked_out_at.is_(None),
                )
                .order_by(GamingBooking.checked_in_at.asc())
            )
        ).all()

        now = datetime.now(UTC)
        live: list[dict] = []
        for booking, resource in rows:
            hours = int(booking.duration_hours or 1) + int(booking.extended_hours or 0)
            ends_at = None
            minutes_remaining = None
            if booking.checked_in_at is not None:
                started = booking.checked_in_at
                if started.tzinfo is None:
                    started = started.replace(tzinfo=UTC)
                ends_at = started + timedelta(hours=hours)
                minutes_remaining = int((ends_at - now).total_seconds() // 60)

            customer_name = booking.guest_name
            if not customer_name and booking.club_customer_id is not None:
                customer = (
                    await self.session.execute(
                        select(ClubCustomer).where(ClubCustomer.id == booking.club_customer_id)
                    )
                ).scalar_one_or_none()
                if customer is not None:
                    customer_name = await self.customers.resolve_name(customer)

            live.append(
                {
                    "booking_id": booking.id,
                    "booking_ref": booking.booking_ref,
                    "resource_id": booking.resource_id,
                    "resource_label": resource.label if resource else None,
                    "resource_type": resource.resource_type if resource else None,
                    "customer_name": customer_name,
                    "contact_phone": booking.contact_phone,
                    "checked_in_at": booking.checked_in_at,
                    "ends_at": ends_at,
                    "minutes_remaining": minutes_remaining,
                    "is_overdue": minutes_remaining is not None and minutes_remaining < 0,
                    "units": booking.units,
                    "amount_paise": booking.amount_paise,
                }
            )
        return live

    async def recent_for_customer(
        self, parlor_id: UUID, customer_id: UUID, limit: int = 20
    ) -> list[GamingBooking]:
        rows = (
            await self.session.execute(
                select(GamingBooking)
                .where(
                    GamingBooking.parlour_id == parlor_id,
                    GamingBooking.club_customer_id == customer_id,
                )
                .order_by(GamingBooking.created_at.desc())
                .limit(limit)
            )
        ).scalars().all()
        return list(rows)

    # ---- internals -------------------------------------------------------------

    async def _free_resource(self, booking: GamingBooking) -> None:
        """Return a resource to available when its session ends, unless staff have put
        it into maintenance/offline in the meantime."""
        if booking.resource_id is None:
            return
        resource = (
            await self.session.execute(
                select(ClubResource).where(ClubResource.id == booking.resource_id)
            )
        ).scalar_one_or_none()
        if resource is None:
            return
        if resource.status in (
            ResourceStatus.MAINTENANCE.value,
            ResourceStatus.OFFLINE.value,
        ):
            return
        resource.status = ResourceStatus.AVAILABLE.value

    def _audit(
        self,
        booking: GamingBooking,
        from_status: str | None,
        to_status: str,
        actor_id: UUID | None,
        reason: str,
    ) -> None:
        self.session.add(
            BookingAudit(
                booking_id=booking.id,
                from_status=from_status,
                to_status=to_status,
                actor="owner",
                actor_id=actor_id,
                reason=reason,
            )
        )


class PricingRuleService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_rules(self, parlor_id: UUID) -> list[ClubPricingRule]:
        rows = (
            await self.session.execute(
                select(ClubPricingRule)
                .where(ClubPricingRule.parlor_id == parlor_id)
                .order_by(ClubPricingRule.priority.desc(), ClubPricingRule.created_at.desc())
            )
        ).scalars().all()
        return list(rows)

    async def get(self, parlor_id: UUID, rule_id: UUID) -> ClubPricingRule:
        rule = (
            await self.session.execute(
                select(ClubPricingRule).where(
                    ClubPricingRule.id == rule_id, ClubPricingRule.parlor_id == parlor_id
                )
            )
        ).scalar_one_or_none()
        if rule is None:
            raise NotFoundError("Pricing rule not found")
        return rule

    async def create(self, parlor_id: UUID, data) -> ClubPricingRule:
        await self._validate_scope(parlor_id, data.scope.value, data.scope_value)
        rule = ClubPricingRule(
            parlor_id=parlor_id,
            name=data.name.strip(),
            scope=data.scope.value,
            scope_value=data.scope_value or "",
            base_rate_paise=data.base_rate_paise,
            time_slabs=[s.model_dump() for s in data.time_slabs] if data.time_slabs else None,
            day_of_week_overrides=data.day_of_week_overrides,
            package_defs=[p.model_dump() for p in data.package_defs] if data.package_defs else None,
            priority=data.priority,
            valid_from=data.valid_from,
            valid_to=data.valid_to,
            is_active=data.is_active,
        )
        self.session.add(rule)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def update(self, parlor_id: UUID, rule_id: UUID, data) -> ClubPricingRule:
        rule = await self.get(parlor_id, rule_id)
        scope = data.scope.value if data.scope is not None else rule.scope
        scope_value = data.scope_value if data.scope_value is not None else rule.scope_value
        await self._validate_scope(parlor_id, scope, scope_value)
        rule.scope = scope
        rule.scope_value = scope_value or ""
        if data.name is not None:
            rule.name = data.name.strip()
        if data.base_rate_paise is not None:
            rule.base_rate_paise = data.base_rate_paise
        if data.time_slabs is not None:
            rule.time_slabs = [s.model_dump() for s in data.time_slabs]
        if data.day_of_week_overrides is not None:
            rule.day_of_week_overrides = data.day_of_week_overrides
        if data.package_defs is not None:
            rule.package_defs = [p.model_dump() for p in data.package_defs]
        for field in ("priority", "valid_from", "valid_to", "is_active"):
            value = getattr(data, field, None)
            if value is not None:
                setattr(rule, field, value)
        await self.session.commit()
        await self.session.refresh(rule)
        return rule

    async def delete(self, parlor_id: UUID, rule_id: UUID) -> None:
        rule = await self.get(parlor_id, rule_id)
        rule.is_active = False
        await self.session.commit()

    async def _validate_scope(self, parlor_id: UUID, scope: str, scope_value: str | None) -> None:
        """A rule must not point at another club's zone/resource — that would leak a
        rate across the tenant boundary."""
        if scope == "zone":
            if not scope_value:
                raise ValidationError("scope_value must be a zone id")
            await ZoneService(self.session).get(parlor_id, _as_uuid(scope_value, "zone id"))
        elif scope == "resource":
            if not scope_value:
                raise ValidationError("scope_value must be a resource id")
            await ResourceService(self.session).get(
                parlor_id, _as_uuid(scope_value, "resource id")
            )
        elif scope == "resource_type":
            if not scope_value:
                raise ValidationError("scope_value must be a resource type")


def _as_uuid(value: str, label: str) -> UUID:
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"Invalid {label}") from exc
