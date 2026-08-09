"""Availability + hold / pay / release + v2 booking (Cashfree).

Correctness: Postgres EXCLUDE on booking_unit_locks (via LockService).
Redis = speed hint. WebSocket = notification.
"""

from datetime import date, time
from uuid import UUID

from fastapi import APIRouter, Header, Query, status
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.dependencies import CurrentUserDep, DbSessionDep, RedisDep
from app.domains.common.exceptions import ValidationError
from app.domains.gaming_booking.availability_service import AvailabilityService
from app.domains.gaming_booking.lock_service import HOLD_MINUTES, LockService
from app.domains.gaming_booking.schemas import GamingBookingResponse
from app.domains.gaming_booking.service import GamingBookingService
from app.domains.payments import cashfree_client

router = APIRouter(tags=["Availability & Booking v2"])


class AvailabilityResponse(BaseModel):
    parlor_id: UUID
    date: date
    station_type: str
    slots: list[dict]
    v: int = 0


class HoldRequest(BaseModel):
    parlor_id: UUID
    station_type: str = Field(default="PC", max_length=20)
    date: date
    start_time: time
    duration_hours: int = Field(default=1, ge=1, le=3)
    units: int = Field(default=1, ge=1, le=4)
    guest_name: str | None = None
    contact_phone: str | None = None
    resource_id: UUID | None = None
    promo_code: str | None = None


class HoldResponse(BaseModel):
    booking: GamingBookingResponse
    expires_at: str
    amount_paise: int | None = None


class CreateBookingV2Request(BaseModel):
    parlor_id: UUID
    station_type: str = Field(default="PC", max_length=20)
    date: date
    start_time: time
    duration_hours: int = Field(default=1, ge=1, le=3)
    units: int = Field(default=1, ge=1, le=4)
    guest_name: str | None = None
    contact_phone: str | None = None
    payment_mode: str = Field(default="online", max_length=30)
    promo_code: str | None = None


class CreateBookingV2Response(BaseModel):
    booking: GamingBookingResponse
    payment_session_id: str | None = None
    cf_order_id: str | None = None
    expires_at: str | None = None
    amount_paise: int | None = None
    mock_mode: bool = False


class PayResponse(BaseModel):
    booking: GamingBookingResponse
    payment_session_id: str | None = None
    cf_order_id: str | None = None
    expires_at: str | None = None
    amount_paise: int | None = None
    mock_mode: bool = False


@router.get("/parlors/{parlor_id}/availability", response_model=AvailabilityResponse)
async def get_availability(
    parlor_id: UUID,
    db: DbSessionDep,
    redis: RedisDep,
    date: date = Query(..., description="YYYY-MM-DD"),
    station_type: str = Query(default="PC"),
) -> AvailabilityResponse:
    snap = await LockService(db, redis).availability_snapshot(parlor_id, date, station_type)
    return AvailabilityResponse(
        parlor_id=parlor_id,
        date=date,
        station_type=station_type,
        slots=snap["slots"],
        v=snap["v"],
    )


@router.get("/clubs/{club_id}/availability", response_model=AvailabilityResponse)
async def get_club_availability(
    club_id: UUID,
    db: DbSessionDep,
    redis: RedisDep,
    date: date = Query(..., description="YYYY-MM-DD"),
    station_type: str = Query(default="PC"),
) -> AvailabilityResponse:
    """Spec snapshot endpoint — same grid as parlor availability + version `v`."""
    return await get_availability(club_id, db, redis, date, station_type)


@router.get("/parlors/{parlor_id}/station-types")
async def list_station_types(parlor_id: UUID, db: DbSessionDep) -> dict:
    types = await AvailabilityService(db).list_station_types(parlor_id)
    return {"parlor_id": str(parlor_id), "station_types": types}


@router.post("/bookings/hold", response_model=HoldResponse, status_code=status.HTTP_200_OK)
async def hold_slot(
    body: HoldRequest,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> HoldResponse:
    if not idempotency_key:
        raise ValidationError("Idempotency-Key header required")
    booking = await LockService(db, redis).acquire_hold(
        user_id=current_user.id,
        parlor_id=body.parlor_id,
        station_type=body.station_type.upper(),
        slot_date=body.date,
        start_time=body.start_time,
        duration_hours=body.duration_hours,
        units=body.units,
        idempotency_key=idempotency_key,
        contact_phone=body.contact_phone
        or getattr(current_user, "phone", None)
        or getattr(current_user, "phone_number", None),
        guest_name=body.guest_name,
        promo_code=body.promo_code,
        resource_id=body.resource_id,
    )
    # Schedule expire (best-effort)
    try:
        from app.tasks.booking_tasks import expire_booking_hold

        expire_booking_hold.apply_async(args=[str(booking.id)], countdown=HOLD_MINUTES * 60)
    except Exception:  # noqa: BLE001
        pass

    resp = await GamingBookingService(db)._to_response(booking)
    return HoldResponse(
        booking=resp,
        expires_at=booking.hold_expires_at.isoformat() if booking.hold_expires_at else "",
        amount_paise=booking.amount_paise,
    )


@router.post("/bookings/{booking_id}/release", response_model=GamingBookingResponse)
async def release_hold(
    booking_id: UUID,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> GamingBookingResponse:
    booking = await LockService(db, redis).release_hold(booking_id, user_id=current_user.id)
    return await GamingBookingService(db)._to_response(booking)


@router.post("/bookings/{booking_id}/pay", response_model=PayResponse)
async def pay_held_booking(
    booking_id: UUID,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> PayResponse:
    """held → payment_pending + Cashfree order; extends expires_at by 5 minutes."""
    svc = LockService(db, redis)
    booking = await svc.start_payment(booking_id, user_id=current_user.id)

    s = get_settings()
    amount_paise = booking.amount_paise or int(float(booking.final_price or 0) * 100)
    order = await cashfree_client.create_order(
        order_id=booking.booking_ref,
        amount_paise=amount_paise,
        customer_id=str(current_user.id),
        customer_phone=booking.contact_phone or "9999999999",
        return_url=s.cashfree_return_url,
        notify_url=s.cashfree_notify_url
        or "https://gamer-circle-api.onrender.com/api/v1/payments/webhooks/cashfree",
        settings=s,
    )
    payment_session_id = order.get("payment_session_id")
    cf_order_id = str(order.get("cf_order_id") or "")
    mock_mode = order.get("status") == "mock"
    booking.cf_order_id = cf_order_id
    booking.payment_session_id = payment_session_id
    await db.commit()
    await db.refresh(booking)

    resp = await GamingBookingService(db)._to_response(booking)
    return PayResponse(
        booking=resp,
        payment_session_id=payment_session_id,
        cf_order_id=cf_order_id,
        expires_at=booking.hold_expires_at.isoformat() if booking.hold_expires_at else None,
        amount_paise=booking.amount_paise,
        mock_mode=mock_mode,
    )


@router.post(
    "/bookings/v2",
    response_model=CreateBookingV2Response,
    status_code=status.HTTP_201_CREATED,
)
async def create_booking_v2(
    body: CreateBookingV2Request,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> CreateBookingV2Response:
    """Compat: hold (+ optional pay) in one call. Prefer /bookings/hold then /pay."""
    if not idempotency_key:
        raise ValidationError("Idempotency-Key header required")
    svc = AvailabilityService(db)
    booking = await svc.create_booking_v2(
        user_id=current_user.id,
        parlor_id=body.parlor_id,
        station_type=body.station_type.upper(),
        slot_date=body.date,
        start_time=body.start_time,
        duration_hours=body.duration_hours,
        units=body.units,
        idempotency_key=idempotency_key,
        contact_phone=body.contact_phone
        or getattr(current_user, "phone", None)
        or getattr(current_user, "phone_number", None),
        guest_name=body.guest_name,
        payment_mode=body.payment_mode,
        promo_code=body.promo_code,
        redis=redis,
    )

    payment_session_id = None
    cf_order_id = None
    mock_mode = False
    if body.payment_mode == "online":
        # Move held → payment_pending and create Cashfree order
        lock = LockService(db, redis)
        if booking.booking_status == "held":
            booking = await lock.start_payment(booking.id, user_id=current_user.id)
        s = get_settings()
        amount_paise = booking.amount_paise or int(float(booking.final_price or 0) * 100)
        order = await cashfree_client.create_order(
            order_id=booking.booking_ref,
            amount_paise=amount_paise,
            customer_id=str(current_user.id),
            customer_phone=booking.contact_phone or "9999999999",
            return_url=s.cashfree_return_url,
            notify_url=s.cashfree_notify_url
            or "https://gamer-circle-api.onrender.com/api/v1/payments/webhooks/cashfree",
            settings=s,
        )
        payment_session_id = order.get("payment_session_id")
        cf_order_id = str(order.get("cf_order_id") or "")
        mock_mode = order.get("status") == "mock"
        booking.cf_order_id = cf_order_id
        booking.payment_session_id = payment_session_id
        await db.commit()
        await db.refresh(booking)

        try:
            from app.tasks.booking_tasks import expire_booking_hold

            expire_booking_hold.apply_async(
                args=[str(booking.id)],
                countdown=HOLD_MINUTES * 60,
            )
        except Exception:  # noqa: BLE001
            pass

    resp = await GamingBookingService(db)._to_response(booking)
    return CreateBookingV2Response(
        booking=resp,
        payment_session_id=payment_session_id,
        cf_order_id=cf_order_id,
        expires_at=booking.hold_expires_at.isoformat() if booking.hold_expires_at else None,
        amount_paise=booking.amount_paise,
        mock_mode=mock_mode,
    )


@router.get("/bookings/{booking_id}/status")
async def booking_status(
    booking_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict:
    booking = await GamingBookingService(db).get_booking(booking_id, user_id=current_user.id)
    if booking.booking_status in ("payment_pending", "held") and getattr(
        booking, "cf_order_id", None
    ):
        try:
            order = await cashfree_client.get_order(booking.cf_order_id or "")
            st = (order.get("order_status") or order.get("status") or "").upper()
            if st in ("PAID", "SUCCESS", "COMPLETED"):
                b = await AvailabilityService(db).confirm_payment(
                    booking_id,
                    cf_reference=booking.cf_order_id,
                    event_id=None,
                    actor="poll",
                )
                booking = await GamingBookingService(db)._to_response(b)
        except Exception:  # noqa: BLE001
            pass
    hold = getattr(booking, "hold_expires_at", None)
    return {
        "id": str(booking.id),
        "booking_status": booking.booking_status,
        "payment_status": booking.payment_status,
        "booking_ref": booking.booking_ref,
        "final_price": str(booking.final_price) if booking.final_price else None,
        "hold_expires_at": hold.isoformat() if hold else None,
    }
