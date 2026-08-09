"""Live availability lock layer — hold / release / pay / confirm.

Postgres EXCLUDE on booking_unit_locks is the source of truth.
Redis SET NX PX is a speed hint only. WebSocket is notification only.

Never SELECT-check-then-INSERT for correctness — insert locks and catch 23P01.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

import redis.asyncio as aioredis
from sqlalchemy import select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.club_ops.pricing import PriceResolver, resource_type_for
from app.domains.club_ops.promotions import PromotionService
from app.domains.common.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from app.domains.gaming_booking.booking_ref import generate_booking_ref
from app.domains.gaming_booking.inventory_models import (
    BookingAudit,
    BookingHold,
    BookingUnitLock,
    ParlorStation,
    PaymentLedger,
)
from app.domains.gaming_booking.models import GamingBooking, GamingSlot
from app.domains.gaming_booking.slot_engine import DEFAULT_CAPACITY, DEFAULT_PRICE, SlotEngine
from app.domains.gaming_place.models import GamingPlace, GamingPlaceExtension
from app.ws.events import publish_event

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")
HOLD_MINUTES = 8
PAYMENT_EXTEND_MINUTES = 5
MAX_ACTIVE_HOLDS = 3
HOLD_ATTEMPTS_PER_MIN = 10
COMMISSION_BPS = 1000
LIVE_STATUSES = ("held", "payment_pending", "confirmed", "checked_in")
RELEASE_LUA = """
if redis.call('get', KEYS[1]) == ARGV[1] then
  return redis.call('del', KEYS[1])
else
  return 0
end
"""


def build_during(
    slot_date: date, start: time, duration_hours: int
) -> tuple[datetime, datetime]:
    """Wall-clock Asia/Kolkata → aware UTC bounds for half-open [start, end)."""
    start_local = datetime.combine(slot_date, start, tzinfo=IST)
    end_local = start_local + timedelta(hours=duration_hours)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def _is_exclusion_violation(exc: BaseException) -> bool:
    orig = getattr(exc, "orig", None)
    sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
    if sqlstate == "23P01":
        return True
    msg = str(exc).lower()
    return "excl_booking_unit" in msg or "exclusion" in msg or "23p01" in msg


class LockService:
    def __init__(self, session: AsyncSession, redis: aioredis.Redis | None = None) -> None:
        self.session = session
        self.redis = redis

    async def _station_capacity(self, parlor_id: UUID, station_type: str) -> tuple[int, int]:
        row = (
            await self.session.execute(
                select(ParlorStation).where(
                    ParlorStation.parlor_id == parlor_id,
                    ParlorStation.station_type == station_type,
                    ParlorStation.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if row:
            return row.total_count, row.hourly_price_paise
        ext = (
            await self.session.execute(
                select(GamingPlaceExtension).where(
                    GamingPlaceExtension.gaming_place_id == parlor_id
                )
            )
        ).scalar_one_or_none()
        price = DEFAULT_PRICE
        if ext and ext.price_per_hour:
            price = Decimal(str(ext.price_per_hour))
        return DEFAULT_CAPACITY, int(price * 100)

    async def _rate_limit_hold(self, user_id: UUID) -> None:
        if self.redis is None:
            return
        # Active holds
        active = (
            await self.session.execute(
                select(GamingBooking.id).where(
                    GamingBooking.user_id == user_id,
                    GamingBooking.booking_status.in_(("held", "payment_pending")),
                )
            )
        ).scalars().all()
        if len(active) >= MAX_ACTIVE_HOLDS:
            raise RateLimitError(f"Max {MAX_ACTIVE_HOLDS} active holds per user")

        key = f"hold:attempts:{user_id}:{datetime.now(UTC).strftime('%Y%m%d%H%M')}"
        n = await self.redis.incr(key)
        if n == 1:
            await self.redis.expire(key, 70)
        if n > HOLD_ATTEMPTS_PER_MIN:
            raise RateLimitError("Too many hold attempts — try again shortly")

    async def _redis_hint_acquire(
        self, parlor_id: UUID, station_type: str, start: datetime, end: datetime, token: str
    ) -> str | None:
        if self.redis is None:
            return None
        key = (
            f"lock:slot:{parlor_id}:{station_type}:"
            f"{start.isoformat()}:{end.isoformat()}"
        )
        ok = await self.redis.set(key, token, nx=True, px=HOLD_MINUTES * 60 * 1000)
        return key if ok else None

    async def _redis_hint_release(self, key: str | None, token: str) -> None:
        if self.redis is None or not key:
            return
        try:
            await self.redis.eval(RELEASE_LUA, 1, key, token)
        except Exception:  # noqa: BLE001
            logger.debug("redis_lock_release_failed key=%s", key)

    async def _bump_avail_version(self, parlor_id: UUID) -> int:
        if self.redis is None:
            return 0
        return int(await self.redis.incr(f"avail:v:{parlor_id}"))

    async def publish_delta(
        self,
        parlor_id: UUID,
        *,
        event_type: str,
        station_type: str,
        during_start: datetime,
        during_end: datetime,
        units: int,
        booking_id: UUID | None = None,
        resource_id: UUID | None = None,
    ) -> int:
        v = await self._bump_avail_version(parlor_id)
        payload = {
            "t": event_type,
            "v": v,
            "club_id": str(parlor_id),
            "station_type": station_type,
            "start": during_start.isoformat(),
            "end": during_end.isoformat(),
            "units": units,
            "booking_id": str(booking_id) if booking_id else None,
            "resource_id": str(resource_id) if resource_id else None,
        }
        if self.redis is not None:
            # Fan-out across uvicorn workers via existing ws:* listener
            await publish_event(self.redis, f"avail:{parlor_id}", event_type, payload)
            await self.redis.publish(f"avail:{parlor_id}", __import__("json").dumps(payload))
        return v

    async def acquire_hold(
        self,
        *,
        user_id: UUID,
        parlor_id: UUID,
        station_type: str,
        slot_date: date,
        start_time: time,
        duration_hours: int,
        units: int,
        idempotency_key: str,
        contact_phone: str | None = None,
        guest_name: str | None = None,
        promo_code: str | None = None,
        resource_id: UUID | None = None,
    ) -> GamingBooking:
        if duration_hours < 1 or duration_hours > 3:
            raise ValidationError("duration_hours must be 1–3")
        if units < 1 or units > 4:
            raise ValidationError("units must be 1–4")
        station_type = station_type.upper()

        existing = (
            await self.session.execute(
                select(GamingBooking).where(GamingBooking.idempotency_key == idempotency_key)
            )
        ).scalar_one_or_none()
        if existing:
            return existing

        await self._rate_limit_hold(user_id)

        place = (
            await self.session.execute(select(GamingPlace).where(GamingPlace.id == parlor_id))
        ).scalar_one_or_none()
        if place is None:
            raise NotFoundError("Parlor not found")

        during_start, during_end = build_during(slot_date, start_time, duration_hours)
        total, _fallback_price = await self._station_capacity(parlor_id, station_type)
        if units > total:
            raise ValidationError("units exceed station capacity")

        hint_token = str(uuid.uuid4())
        hint_key = await self._redis_hint_acquire(
            parlor_id, station_type, during_start, during_end, hint_token
        )
        # Hint miss is OK — Postgres EXCLUDE is authoritative. Hint hit just reduces load.

        resource_type = resource_type_for(station_type)
        breakdown = await PriceResolver(self.session).resolve(
            parlor_id=parlor_id,
            resource_type=resource_type,
            booking_date=slot_date,
            start_time=start_time,
            duration_hours=duration_hours,
            units=units,
        )
        subtotal_paise = breakdown.subtotal_paise

        from app.domains.club_ops.service import CustomerService

        club_customer = await CustomerService(self.session).ensure_for_user(parlor_id, user_id)
        if club_customer.is_banned:
            raise ValidationError("You are not permitted to book at this club")

        promo_outcome = await PromotionService(self.session).apply_best(
            parlor_id=parlor_id,
            subtotal_paise=subtotal_paise,
            resource_type=resource_type,
            booking_date=slot_date,
            start_time=start_time,
            code=promo_code,
            club_customer_id=club_customer.id,
        )
        if promo_code and not promo_outcome.valid:
            raise ValidationError(promo_outcome.reason or "Promotion is not valid")

        club_discount = promo_outcome.discount_paise if promo_outcome.valid else 0
        price_paise = max(0, subtotal_paise - club_discount)
        commission = (price_paise * COMMISSION_BPS) // 10000
        amount = Decimal(price_paise) / Decimal(100)
        end_time = (datetime.combine(slot_date, start_time) + timedelta(hours=duration_hours)).time()
        expires = datetime.now(UTC) + timedelta(minutes=HOLD_MINUTES)

        # Try unit-index assignments until EXCLUDE accepts or capacity exhausted.
        # Correctness = INSERT + catch 23P01 — never "SELECT free then INSERT".
        last_err: Exception | None = None
        for offset in range(total):
            indices = [(offset + i) % total for i in range(units)]
            # Skip duplicate indices when units wrap (units > total already rejected)
            if len(set(indices)) != units:
                continue
            try:
                booking = await self._insert_hold_with_units(
                    user_id=user_id,
                    parlor_id=parlor_id,
                    station_type=station_type,
                    slot_date=slot_date,
                    start_time=start_time,
                    end_time=end_time,
                    duration_hours=duration_hours,
                    units=units,
                    during_start=during_start,
                    during_end=during_end,
                    expires=expires,
                    idempotency_key=idempotency_key,
                    contact_phone=contact_phone,
                    guest_name=guest_name,
                    price_paise=price_paise,
                    commission=commission,
                    amount=amount,
                    breakdown_base=breakdown.base_rate_paise,
                    subtotal_paise=subtotal_paise,
                    club_customer_id=club_customer.id,
                    club_promotion_id=promo_outcome.promotion_id if promo_outcome.valid else None,
                    club_discount=club_discount,
                    unit_indices=indices,
                    resource_id=resource_id,
                    fallback_hourly_paise=_fallback_price,
                )
                if promo_outcome.valid and promo_outcome.promotion_id is not None:
                    promo_row = await PromotionService(self.session).get_scoped(
                        parlor_id, promo_outcome.promotion_id
                    )
                    await PromotionService(self.session).consume(promo_row)

                await self.session.commit()
                await self.session.refresh(booking)
                await self.publish_delta(
                    parlor_id,
                    event_type="slot_held",
                    station_type=station_type,
                    during_start=during_start,
                    during_end=during_end,
                    units=units,
                    booking_id=booking.id,
                    resource_id=resource_id,
                )
                return booking
            except IntegrityError as exc:
                await self.session.rollback()
                last_err = exc
                if _is_exclusion_violation(exc):
                    continue
                # Unique idempotency race — return existing
                again = (
                    await self.session.execute(
                        select(GamingBooking).where(
                            GamingBooking.idempotency_key == idempotency_key
                        )
                    )
                ).scalar_one_or_none()
                if again:
                    return again
                raise

        await self._redis_hint_release(hint_key, hint_token)
        raise ConflictError(
            "Someone just took this slot — pick another",
            details={"reason": "exclude_violation", "last": str(last_err) if last_err else None},
        )

    async def _insert_hold_with_units(
        self,
        *,
        user_id: UUID,
        parlor_id: UUID,
        station_type: str,
        slot_date: date,
        start_time: time,
        end_time: time,
        duration_hours: int,
        units: int,
        during_start: datetime,
        during_end: datetime,
        expires: datetime,
        idempotency_key: str,
        contact_phone: str | None,
        guest_name: str | None,
        price_paise: int,
        commission: int,
        amount: Decimal,
        breakdown_base: int,
        subtotal_paise: int,
        club_customer_id: UUID,
        club_promotion_id: UUID | None,
        club_discount: int,
        unit_indices: list[int],
        resource_id: UUID | None,
        fallback_hourly_paise: int,
    ) -> GamingBooking:
        engine = SlotEngine(self.session)
        await engine.ensure_slots_for_date(parlor_id, slot_date)
        slot = (
            await self.session.execute(
                select(GamingSlot).where(
                    GamingSlot.parlour_id == parlor_id,
                    GamingSlot.slot_date == slot_date,
                    GamingSlot.start_time == start_time,
                )
            )
        ).scalar_one_or_none()
        if slot is None:
            slot = GamingSlot(
                parlour_id=parlor_id,
                slot_date=slot_date,
                start_time=start_time,
                end_time=end_time,
                price_per_hour=Decimal(fallback_hourly_paise) / 100,
                max_players=max(unit_indices) + 1 if unit_indices else 1,
                current_bookings=0,
                is_available=True,
            )
            self.session.add(slot)
            await self.session.flush()

        booking_ref = await generate_booking_ref(self.session)
        free_cancel = datetime.combine(slot_date, start_time, tzinfo=IST).astimezone(UTC) - timedelta(
            hours=2
        )
        booking = GamingBooking(
            booking_ref=booking_ref,
            user_id=user_id,
            parlour_id=parlor_id,
            slot_id=slot.id,
            guest_name=guest_name,
            num_players=units,
            slot_date=slot_date,
            start_time=start_time,
            end_time=end_time,
            hours_booked=Decimal(duration_hours),
            price_per_hour=Decimal(breakdown_base) / 100,
            total_price=Decimal(subtotal_paise) / Decimal(100),
            tax_amount=Decimal("0"),
            discount_amount=Decimal("0"),
            final_price=amount,
            payment_mode="online",
            payment_status="pending",
            booking_status="held",
            free_cancellation_before=free_cancel,
            is_non_refundable=False,
            contact_phone=contact_phone,
            station_type=station_type,
            duration_hours=duration_hours,
            units=units,
            amount_paise=price_paise,
            commission_paise=commission,
            idempotency_key=idempotency_key,
            hold_expires_at=expires,
            during_start=during_start,
            during_end=during_end,
            club_promotion_id=club_promotion_id,
            club_discount_paise=club_discount,
            club_customer_id=club_customer_id,
            resource_id=resource_id,
            updated_at=datetime.now(UTC),
        )
        self.session.add(booking)
        await self.session.flush()

        for idx in unit_indices:
            self.session.add(
                BookingUnitLock(
                    booking_id=booking.id,
                    parlor_id=parlor_id,
                    station_type=station_type,
                    unit_index=idx,
                    resource_id=resource_id if len(unit_indices) == 1 else None,
                    during_start=during_start,
                    during_end=during_end,
                    is_active=True,
                )
            )

        self.session.add(
            BookingHold(
                booking_id=booking.id,
                parlor_id=parlor_id,
                station_type=station_type,
                date=slot_date,
                start_time=start_time,
                duration_hours=duration_hours,
                units=units,
                expires_at=expires,
                released=False,
            )
        )
        self.session.add(
            BookingAudit(
                booking_id=booking.id,
                from_status=None,
                to_status="held",
                actor="user",
                actor_id=user_id,
                reason="hold_acquired",
            )
        )
        # Flush so EXCLUDE fires before commit
        await self.session.flush()
        return booking

    async def release_hold(self, booking_id: UUID, *, user_id: UUID | None = None) -> GamingBooking:
        booking = (
            await self.session.execute(
                select(GamingBooking).where(GamingBooking.id == booking_id).with_for_update()
            )
        ).scalar_one_or_none()
        if booking is None:
            raise NotFoundError("Booking not found")
        if user_id is not None and booking.user_id != user_id:
            raise ForbiddenError("Not your booking")
        if booking.booking_status not in ("held", "payment_pending"):
            raise ValidationError(f"Cannot release status={booking.booking_status}")

        result = await self.session.execute(
            update(GamingBooking)
            .where(
                GamingBooking.id == booking_id,
                GamingBooking.booking_status.in_(("held", "payment_pending")),
            )
            .values(
                booking_status="cancelled",
                cancelled_by="user" if user_id else "system",
                cancelled_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            .returning(GamingBooking.id)
        )
        if result.first() is None:
            raise ConflictError("Booking state changed — refresh and retry")

        await self.session.execute(
            update(BookingUnitLock)
            .where(BookingUnitLock.booking_id == booking_id, BookingUnitLock.is_active.is_(True))
            .values(is_active=False)
        )
        hold = (
            await self.session.execute(
                select(BookingHold).where(BookingHold.booking_id == booking_id).with_for_update()
            )
        ).scalar_one_or_none()
        if hold and not hold.released:
            hold.released = True

        self.session.add(
            BookingAudit(
                booking_id=booking_id,
                from_status=booking.booking_status,
                to_status="cancelled",
                actor="user" if user_id else "system",
                actor_id=user_id,
                reason="hold_released",
            )
        )
        await self.session.commit()
        await self.session.refresh(booking)

        if booking.during_start and booking.during_end and booking.station_type:
            await self.publish_delta(
                booking.parlour_id,
                event_type="slot_released",
                station_type=booking.station_type,
                during_start=booking.during_start,
                during_end=booking.during_end,
                units=booking.units or 1,
                booking_id=booking.id,
            )
        return booking

    async def start_payment(self, booking_id: UUID, *, user_id: UUID) -> GamingBooking:
        """held → payment_pending; extend expires_at by PAYMENT_EXTEND_MINUTES."""
        result = await self.session.execute(
            update(GamingBooking)
            .where(
                GamingBooking.id == booking_id,
                GamingBooking.user_id == user_id,
                GamingBooking.booking_status == "held",
            )
            .values(
                booking_status="payment_pending",
                hold_expires_at=datetime.now(UTC) + timedelta(minutes=PAYMENT_EXTEND_MINUTES),
                updated_at=datetime.now(UTC),
            )
            .returning(GamingBooking.id)
        )
        row = result.first()
        if row is None:
            booking = (
                await self.session.execute(
                    select(GamingBooking).where(GamingBooking.id == booking_id)
                )
            ).scalar_one_or_none()
            if booking is None:
                raise NotFoundError("Booking not found")
            if booking.user_id != user_id:
                raise ForbiddenError("Not your booking")
            if booking.booking_status == "payment_pending":
                return booking
            raise ConflictError(f"Cannot pay from status={booking.booking_status}")

        await self.session.execute(
            update(BookingHold)
            .where(BookingHold.booking_id == booking_id, BookingHold.released.is_(False))
            .values(expires_at=datetime.now(UTC) + timedelta(minutes=PAYMENT_EXTEND_MINUTES))
        )
        self.session.add(
            BookingAudit(
                booking_id=booking_id,
                from_status="held",
                to_status="payment_pending",
                actor="user",
                actor_id=user_id,
                reason="payment_started",
            )
        )
        await self.session.commit()
        booking = (
            await self.session.execute(select(GamingBooking).where(GamingBooking.id == booking_id))
        ).scalar_one()
        return booking

    async def confirm_payment(
        self,
        booking_id: UUID,
        *,
        cf_reference: str | None,
        event_id: str | None,
        actor: str = "webhook",
    ) -> GamingBooking:
        """Webhook-authoritative confirm with guarded status transition.

        Late pay after expiry → refund_pending + enqueue auto_refund. Never overwrite
        another user's confirmed booking (locks already released on expire).
        """
        booking = (
            await self.session.execute(
                select(GamingBooking).where(GamingBooking.id == booking_id).with_for_update()
            )
        ).scalar_one_or_none()
        if booking is None:
            raise NotFoundError("Booking not found")

        if booking.booking_status == "confirmed" and booking.payment_status == "paid":
            return booking

        if booking.booking_status in ("expired", "cancelled", "failed"):
            # Money arrived after slot was released — refund, do not revive locks.
            result = await self.session.execute(
                update(GamingBooking)
                .where(
                    GamingBooking.id == booking_id,
                    GamingBooking.booking_status.in_(("expired", "cancelled", "failed")),
                )
                .values(
                    booking_status="refund_pending",
                    payment_status="paid",
                    payment_id=cf_reference,
                    updated_at=datetime.now(UTC),
                )
                .returning(GamingBooking.id)
            )
            if result.first():
                self.session.add(
                    BookingAudit(
                        booking_id=booking_id,
                        from_status=booking.booking_status,
                        to_status="refund_pending",
                        actor=actor,
                        reason="payment_after_expiry",
                    )
                )
                amount = booking.amount_paise or int(float(booking.final_price or 0) * 100)
                self.session.add(
                    PaymentLedger(
                        booking_id=booking.id,
                        entry_type="payment",
                        amount_paise=amount,
                        cf_reference=cf_reference,
                        cf_event_id=event_id,
                        balance_direction="credit",
                    )
                )
                await self.session.commit()
                try:
                    from app.tasks.booking_tasks import auto_refund

                    auto_refund.delay(str(booking_id), cf_reference or "", event_id or "")
                except Exception:  # noqa: BLE001
                    logger.exception("auto_refund_enqueue_failed")
            await self.session.refresh(booking)
            return booking

        result = await self.session.execute(
            update(GamingBooking)
            .where(
                GamingBooking.id == booking_id,
                GamingBooking.booking_status.in_(("held", "payment_pending")),
            )
            .values(
                booking_status="confirmed",
                payment_status="paid",
                payment_id=cf_reference,
                updated_at=datetime.now(UTC),
            )
            .returning(GamingBooking.id)
        )
        if result.first() is None:
            # Lost race — re-read
            await self.session.refresh(booking)
            if booking.booking_status == "confirmed":
                return booking
            raise ConflictError("Booking could not be confirmed")

        await self.session.execute(
            update(BookingHold)
            .where(BookingHold.booking_id == booking_id)
            .values(released=True)
        )
        # Locks stay active for confirmed occupancy until checkout/cancel/complete.

        amount = booking.amount_paise or int(float(booking.final_price or 0) * 100)
        self.session.add(
            PaymentLedger(
                booking_id=booking.id,
                entry_type="payment",
                amount_paise=amount,
                cf_reference=cf_reference,
                cf_event_id=event_id,
                balance_direction="credit",
            )
        )
        if booking.commission_paise:
            self.session.add(
                PaymentLedger(
                    booking_id=booking.id,
                    entry_type="commission",
                    amount_paise=booking.commission_paise,
                    cf_reference=cf_reference,
                    balance_direction="debit",
                )
            )
        self.session.add(
            BookingAudit(
                booking_id=booking.id,
                from_status="payment_pending",
                to_status="confirmed",
                actor=actor,
                reason="payment_success",
            )
        )
        await self.session.commit()
        await self.session.refresh(booking)

        if booking.during_start and booking.during_end and booking.station_type:
            await self.publish_delta(
                booking.parlour_id,
                event_type="slot_confirmed",
                station_type=booking.station_type,
                during_start=booking.during_start,
                during_end=booking.during_end,
                units=booking.units or 1,
                booking_id=booking.id,
            )
        try:
            from app.tasks.booking_tasks import send_booking_confirmation

            send_booking_confirmation.delay(str(booking.id))
        except Exception:  # noqa: BLE001
            pass
        return booking

    async def expire_stale_holds(self) -> list[dict[str, Any]]:
        """Set-based expire of held/payment_pending past hold_expires_at. Returns released rows."""
        now = datetime.now(UTC)
        # Mark bookings expired
        result = await self.session.execute(
            text(
                """
                UPDATE gaming_bookings
                SET booking_status = 'expired',
                    updated_at = :now,
                    cancelled_by = 'system'
                WHERE booking_status IN ('held', 'payment_pending')
                  AND hold_expires_at IS NOT NULL
                  AND hold_expires_at <= :now
                RETURNING id, parlour_id, station_type, during_start, during_end, units
                """
            ),
            {"now": now},
        )
        rows = [dict(r._mapping) for r in result]

        if rows:
            ids = [r["id"] for r in rows]
            await self.session.execute(
                update(BookingUnitLock)
                .where(BookingUnitLock.booking_id.in_(ids), BookingUnitLock.is_active.is_(True))
                .values(is_active=False)
            )
            await self.session.execute(
                update(BookingHold)
                .where(BookingHold.booking_id.in_(ids), BookingHold.released.is_(False))
                .values(released=True)
            )
            for r in rows:
                self.session.add(
                    BookingAudit(
                        booking_id=r["id"],
                        from_status="held",
                        to_status="expired",
                        actor="system",
                        reason="hold_expired",
                    )
                )
            await self.session.commit()
            for r in rows:
                if r.get("during_start") and r.get("during_end") and r.get("station_type"):
                    await self.publish_delta(
                        r["parlour_id"],
                        event_type="slot_released",
                        station_type=r["station_type"],
                        during_start=r["during_start"],
                        during_end=r["during_end"],
                        units=r.get("units") or 1,
                        booking_id=r["id"],
                    )
        else:
            await self.session.commit()
        return rows

    async def availability_snapshot(
        self, parlor_id: UUID, d: date, station_type: str
    ) -> dict[str, Any]:
        """Grid + monotonic version. WS is optional; this is authoritative."""
        from app.domains.gaming_booking.availability_service import AvailabilityService

        slots = await AvailabilityService(self.session).compute_availability(
            parlor_id, d, station_type.upper()
        )
        v = 0
        if self.redis is not None:
            raw = await self.redis.get(f"avail:v:{parlor_id}")
            v = int(raw or 0)
        return {
            "parlor_id": str(parlor_id),
            "date": d.isoformat(),
            "station_type": station_type.upper(),
            "v": v,
            "slots": slots,
        }
