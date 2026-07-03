"""Booking domain business logic — Redis lock + row-level locking."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.booking.repository import BookingRepository
from app.domains.booking.schemas import BookingResponse
from app.domains.common.exceptions import NotFoundError, ValidationError
from app.domains.parlor.repository import ParlorRepository
from app.domains.tournament.models import Booking, Tournament


class BookingService:
    """Tournament slot booking with concurrency-safe locking."""

    CANCEL_WINDOW = timedelta(hours=2)

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = BookingRepository(session)
        self.parlor_repo = ParlorRepository(session)

    async def book_slot(
        self,
        tournament_id: UUID,
        user_id: UUID,
        redis: aioredis.Redis,
    ) -> BookingResponse:
        lock_key = f"lock:tournament:{tournament_id}:booking"
        acquired = await redis.set(lock_key, "1", nx=True, ex=5)
        if not acquired:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Try again in a moment",
            )

        try:
            result = await self.session.execute(
                select(Tournament)
                .where(Tournament.id == tournament_id)
                .with_for_update()
            )
            tournament = result.scalar_one_or_none()
            if tournament is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
            if tournament.status not in {"open", "full"}:
                raise ValidationError("Tournament is not open for booking")
            if tournament.booked_slots >= tournament.total_slots:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Sold out")

            existing = await self.repo.get_by_tournament_and_user(tournament_id, user_id)
            if existing is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Already booked",
                )

            slot_num = tournament.booked_slots + 1
            payment_status = "paid" if tournament.entry_fee <= 0 else "pending"
            booking = Booking(
                tournament_id=tournament_id,
                user_id=user_id,
                slot_number=slot_num,
                payment_status=payment_status,
            )
            tournament.booked_slots = slot_num
            if tournament.booked_slots >= tournament.total_slots:
                tournament.status = "full"

            await self.repo.create(booking)
            await self.session.commit()
            await self.session.refresh(booking)
            try:
                from app.domains.notification.service import NotificationService
                from app.ws.events import publish_event

                await NotificationService(self.session).create_notification(
                    user_id,
                    "booking_confirmed",
                    "Slot booked!",
                    f"You secured slot #{slot_num} for {tournament.title}.",
                    {"tournament_id": str(tournament_id), "booking_id": str(booking.id)},
                    redis=redis,
                )
                await publish_event(
                    redis,
                    f"tournament:{tournament_id}",
                    "slot_booked",
                    {"booked_slots": slot_num, "tournament_id": str(tournament_id)},
                )
                await redis.delete(f"tournament:{tournament_id}")
            except Exception:
                pass
            return BookingResponse.model_validate(booking)
        finally:
            await redis.delete(lock_key)

    async def create_payment_order(self, booking_id: UUID, user_id: UUID) -> dict[str, str | int]:
        booking = await self.repo.get_by_id(booking_id)
        if booking is None or booking.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        if booking.payment_status == "paid":
            raise ValidationError("Already paid")

        result = await self.session.execute(
            select(Tournament).where(Tournament.id == booking.tournament_id)
        )
        tournament = result.scalar_one_or_none()
        if tournament is None:
            raise NotFoundError("Tournament not found")

        amount_paise = int(tournament.entry_fee * 100)
        from app.domains.payments.razorpay_stub import create_order

        order = create_order(amount_paise, f"booking_{booking_id}")
        if order.get("status") == "not_configured":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Razorpay not configured",
            )
        return {
            "booking_id": str(booking_id),
            "order_id": order["order_id"],
            "amount_paise": amount_paise,
            "currency": "INR",
            "key_id": order.get("key_id"),
        }

    async def confirm_payment(
        self,
        booking_id: UUID,
        user_id: UUID,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> BookingResponse:
        booking = await self.repo.get_by_id(booking_id)
        if booking is None or booking.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

        from app.domains.payments.razorpay_stub import verify_payment_stub

        try:
            result = verify_payment_stub(order_id, payment_id, signature)
        except Exception as exc:
            raise ValidationError(f"Payment verification failed: {exc}") from exc
        if result.get("status") == "not_configured":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Razorpay not configured",
            )

        booking.payment_status = "paid"
        booking.payment_id = payment_id
        await self.session.commit()
        await self.session.refresh(booking)
        return BookingResponse.model_validate(booking)

    async def cancel_booking(self, booking_id: UUID, user_id: UUID) -> BookingResponse:
        booking = await self.repo.get_by_id(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        if booking.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only cancel your own booking",
            )
        if booking.status == "cancelled":
            raise ValidationError("Booking is already cancelled")

        result = await self.session.execute(
            select(Tournament)
            .where(Tournament.id == booking.tournament_id)
            .with_for_update()
        )
        tournament = result.scalar_one_or_none()
        if tournament is None:
            raise NotFoundError("Tournament not found")

        now = datetime.now(UTC)
        if tournament.start_time - now <= self.CANCEL_WINDOW:
            raise ValidationError("Cancellations are only allowed more than 2 hours before start")

        booking.status = "cancelled"
        if tournament.booked_slots > 0:
            tournament.booked_slots -= 1
        if tournament.status == "full" and tournament.booked_slots < tournament.total_slots:
            tournament.status = "open"

        await self.session.commit()
        await self.session.refresh(booking)
        return BookingResponse.model_validate(booking)

    async def list_tournament_bookings(
        self,
        tournament_id: UUID,
        owner_id: UUID,
    ) -> list[BookingResponse]:
        tournament = await self._get_tournament_or_404(tournament_id)
        if not await self.parlor_repo.is_owned_by(tournament.parlor_id, owner_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the parlor owner can view attendees",
            )

        bookings = await self.repo.list_by_tournament(tournament_id)
        return [BookingResponse.model_validate(b) for b in bookings]

    async def list_user_bookings(
        self,
        user_id: UUID,
        *,
        upcoming: bool | None = None,
    ) -> list[BookingResponse]:
        bookings = await self.repo.list_by_user(user_id, upcoming=upcoming)
        return [BookingResponse.model_validate(b) for b in bookings]

    async def _get_tournament_or_404(self, tournament_id: UUID) -> Tournament:
        result = await self.session.execute(
            select(Tournament).where(Tournament.id == tournament_id)
        )
        tournament = result.scalar_one_or_none()
        if tournament is None:
            raise NotFoundError("Tournament not found")
        return tournament