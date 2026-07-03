"""Tournament domain data access layer."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.tournament.models import Booking, Tournament


class TournamentRepository:
    """Repository for tournament persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, tournament_id: UUID) -> Tournament | None:
        result = await self.session.execute(
            select(Tournament).where(Tournament.id == tournament_id)
        )
        return result.scalar_one_or_none()

    async def list_by_parlor(
        self,
        parlor_id: UUID,
        *,
        status: str | None = None,
        upcoming: bool | None = None,
    ) -> list[Tournament]:
        query = select(Tournament).where(Tournament.parlor_id == parlor_id)
        if status is not None:
            query = query.where(Tournament.status == status)
        if upcoming:
            query = query.where(Tournament.start_time > datetime.now(UTC))
        query = query.order_by(Tournament.start_time.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def user_has_booking(self, tournament_id: UUID, user_id: UUID) -> bool:
        result = await self.session.execute(
            select(Booking.id).where(
                Booking.tournament_id == tournament_id,
                Booking.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def create(self, tournament: Tournament) -> Tournament:
        self.session.add(tournament)
        await self.session.flush()
        await self.session.refresh(tournament)
        return tournament

    async def delete(self, tournament: Tournament) -> None:
        await self.session.delete(tournament)
        await self.session.flush()