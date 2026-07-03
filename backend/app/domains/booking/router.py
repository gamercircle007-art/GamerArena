"""
Booking domain API routes.

| Method | Endpoint                        | Auth  | Description           |
|--------|---------------------------------|-------|-----------------------|
| POST   | /tournaments/{id}/book          | User  | Book a slot           |
| DELETE | /bookings/{id}                  | User  | Cancel booking        |
| GET    | /tournaments/{id}/bookings      | Owner | List attendees        |
"""

from uuid import UUID

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUserDep, DbSessionDep, RedisDep
from app.domains.booking.schemas import BookingResponse
from app.domains.booking.service import BookingService

router = APIRouter(tags=["Bookings"])


@router.post(
    "/tournaments/{tournament_id}/book",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a tournament slot",
    description="Uses Redis distributed lock + SELECT FOR UPDATE to prevent double booking.",
)
async def book_tournament_slot(
    tournament_id: UUID,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> BookingResponse:
    service = BookingService(db)
    return await service.book_slot(tournament_id, current_user.id, redis)


@router.delete(
    "/bookings/{booking_id}",
    response_model=BookingResponse,
    summary="Cancel a booking",
    description="Allowed only more than 2 hours before tournament start.",
)
async def cancel_booking(
    booking_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> BookingResponse:
    service = BookingService(db)
    return await service.cancel_booking(booking_id, current_user.id)


@router.get(
    "/tournaments/{tournament_id}/bookings",
    response_model=list[BookingResponse],
    summary="List tournament attendees",
    description="Parlor owner only.",
)
async def list_tournament_bookings(
    tournament_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> list[BookingResponse]:
    service = BookingService(db)
    return await service.list_tournament_bookings(tournament_id, current_user.id)