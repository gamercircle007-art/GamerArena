"""Booking domain data access layer."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.tournament.models import Booking, Tournament


class BookingRepository:
    """Repository for booking persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, booking_id: UUID) -> Booking | None:
        result = await self.session.execute(select(Booking).where(Booking.id == booking_id))
        return result.scalar_one_or_none()

    async def get_by_tournament_and_user(
        self,
        tournament_id: UUID,
        user_id: UUID,
    ) -> Booking | None:
        result = await self.session.execute(
            select(Booking).where(
                Booking.tournament_id == tournament_id,
                Booking.user_id == user_id,
                Booking.status != "cancelled",
            )
        )
        return result.scalar_one_or_none()

    async def list_by_tournament(self, tournament_id: UUID) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(
                Booking.tournament_id == tournament_id,
                Booking.status != "cancelled",
            )
            .order_by(Booking.slot_number.asc())
        )
        return list(result.scalars().all())

    async def list_by_user(
        self,
        user_id: UUID,
        *,
        upcoming: bool | None = None,
    ) -> list[Booking]:
        query = (
            select(Booking)
            .join(Tournament, Booking.tournament_id == Tournament.id)
            .where(Booking.user_id == user_id, Booking.status != "cancelled")
        )
        if upcoming is True:
            query = query.where(Tournament.start_time > datetime.now(UTC))
        elif upcoming is False:
            query = query.where(Tournament.start_time <= datetime.now(UTC))
        query = query.order_by(Tournament.start_time.asc())
        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

    async def create(self, booking: Booking) -> Booking:
        self.session.add(booking)
        await self.session.flush()
        await self.session.refresh(booking)
        return booking