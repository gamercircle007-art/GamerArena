"""Gaming parlor booking API routes (OYO-style)."""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUserDep, DbSessionDep, RedisDep
from app.domains.gaming_booking.schemas import (
    CancelBookingRequest,
    CancellationReasonResponse,
    CompletePaymentRequest,
    CompletePaymentResponse,
    CreateGamingBookingRequest,
    GamingBookingListResponse,
    GamingBookingResponse,
    PaymentOptionsResponse,
    UpdateGuestNameRequest,
    UpdateGstinRequest,
)
from app.domains.gaming_booking.service import GamingBookingService

router = APIRouter(tags=["Gaming Bookings"])


@router.post(
    "/bookings",
    response_model=GamingBookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a gaming parlor booking",
)
async def create_gaming_booking(
    body: CreateGamingBookingRequest,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> GamingBookingResponse:
    return await GamingBookingService(db).create_booking(current_user.id, body, redis=redis)


@router.get("/bookings/{booking_id}", response_model=GamingBookingResponse)
async def get_gaming_booking(
    booking_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> GamingBookingResponse:
    return await GamingBookingService(db).get_booking(booking_id, current_user.id)


@router.get("/bookings/ref/{booking_ref}", response_model=GamingBookingResponse)
async def get_gaming_booking_by_ref(
    booking_ref: str,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> GamingBookingResponse:
    return await GamingBookingService(db).get_booking_by_ref(booking_ref, current_user.id)


@router.get("/users/me/gaming-bookings", response_model=GamingBookingListResponse)
async def list_my_gaming_bookings(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
) -> GamingBookingListResponse:
    items, total = await GamingBookingService(db).get_user_bookings(
        current_user.id, status_filter=status_filter, page=page, limit=limit
    )
    return GamingBookingListResponse(items=items, total=total)


@router.patch("/bookings/{booking_id}/guest-name", response_model=GamingBookingResponse)
async def update_booking_guest_name(
    booking_id: UUID,
    body: UpdateGuestNameRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> GamingBookingResponse:
    return await GamingBookingService(db).update_guest_name(
        booking_id, current_user.id, body.guest_name
    )


@router.patch("/bookings/{booking_id}/gstin", response_model=GamingBookingResponse)
async def update_booking_gstin(
    booking_id: UUID,
    body: UpdateGstinRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> GamingBookingResponse:
    return await GamingBookingService(db).update_gstin(booking_id, current_user.id, body.gstin)


@router.get("/bookings/{booking_id}/payment-options", response_model=PaymentOptionsResponse)
async def get_booking_payment_options(
    booking_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> PaymentOptionsResponse:
    return await GamingBookingService(db).get_payment_options(booking_id, current_user.id)


@router.post("/bookings/{booking_id}/pay", response_model=CompletePaymentResponse)
async def complete_booking_payment(
    booking_id: UUID,
    body: CompletePaymentRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> CompletePaymentResponse:
    booking, points = await GamingBookingService(db).complete_payment(
        booking_id, current_user.id, body
    )
    return CompletePaymentResponse(booking=booking, gc_points_earned=points)


@router.post("/bookings/{booking_id}/cancel", response_model=GamingBookingResponse)
async def cancel_gaming_booking(
    booking_id: UUID,
    body: CancelBookingRequest,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> GamingBookingResponse:
    return await GamingBookingService(db).cancel_booking(booking_id, current_user.id, body)


@router.get("/cancellation-reasons", response_model=list[CancellationReasonResponse])
async def list_cancellation_reasons(db: DbSessionDep) -> list[CancellationReasonResponse]:
    from app.domains.gaming_booking.repository import GamingBookingRepository

    reasons = await GamingBookingRepository(db).list_cancellation_reasons()
    return [CancellationReasonResponse.model_validate(r) for r in reasons]