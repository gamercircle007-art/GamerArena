"""Tournament domain business logic."""

import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

TOURNAMENT_CACHE_TTL = 30

from app.domains.common.exceptions import NotFoundError, ValidationError
from app.domains.parlor.repository import ParlorRepository
from app.domains.parlor.schemas import ParlorSummary
from app.domains.tournament.models import Tournament
from app.domains.tournament.repository import TournamentRepository
from app.domains.tournament.schemas import TournamentCreate, TournamentResponse, TournamentUpdate
from app.domains.user.models import UserRole


class TournamentService:
    """Orchestrates tournament CRUD and listing."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = TournamentRepository(session)
        self.parlor_repo = ParlorRepository(session)

    async def create_tournament(
        self,
        owner_id: UUID,
        data: TournamentCreate,
        *,
        user_role: str | None = None,
    ) -> TournamentResponse:
        if user_role != UserRole.PARLOR_OWNER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only parlor owners can create tournaments",
            )

        parlor = await self.parlor_repo.get_by_owner_id(owner_id)
        if parlor is None:
            raise ValidationError("Create a parlor profile before posting tournaments")

        tournament = Tournament(
            parlor_id=parlor.id,
            title=data.title.strip(),
            game_type=data.game_type.strip().upper(),
            format=data.format.strip(),
            start_time=data.start_time,
            end_time=data.end_time,
            total_slots=data.total_slots,
            booked_slots=0,
            entry_fee=data.entry_fee,
            prizes=data.prizes,
            rules=data.rules,
            status="open",
        )
        created = await self.repo.create(tournament)
        await self.session.commit()
        await self.session.refresh(created)
        return await self._to_response(created, owner_id)

    async def get_tournament(
        self,
        tournament_id: UUID,
        viewer_id: UUID | None = None,
        redis: aioredis.Redis | None = None,
    ) -> TournamentResponse:
        cache_key = f"tournament:{tournament_id}"
        if redis is not None:
            cached = await redis.get(cache_key)
            if cached:
                data = json.loads(cached)
                if viewer_id:
                    data["is_booked_by_me"] = await self.repo.user_has_booking(
                        tournament_id, viewer_id
                    )
                return TournamentResponse.model_validate(data)
        tournament = await self.repo.get_by_id(tournament_id)
        if tournament is None:
            raise NotFoundError("Tournament not found")
        response = await self._to_response(tournament, viewer_id)
        if redis is not None:
            await redis.set(
                cache_key,
                response.model_dump_json(),
                ex=TOURNAMENT_CACHE_TTL,
            )
        return response

    async def update_tournament(
        self,
        tournament_id: UUID,
        owner_id: UUID,
        data: TournamentUpdate,
    ) -> TournamentResponse:
        tournament = await self._get_owned_tournament(tournament_id, owner_id)
        updates = data.model_dump(exclude_unset=True)

        if "title" in updates and updates["title"] is not None:
            tournament.title = updates["title"].strip()
        if "game_type" in updates and updates["game_type"] is not None:
            tournament.game_type = updates["game_type"].strip().upper()
        if "format" in updates and updates["format"] is not None:
            tournament.format = updates["format"].strip()
        if "start_time" in updates:
            tournament.start_time = updates["start_time"]
        if "end_time" in updates:
            tournament.end_time = updates["end_time"]
        if "total_slots" in updates and updates["total_slots"] is not None:
            if updates["total_slots"] < tournament.booked_slots:
                raise ValidationError("total_slots cannot be less than booked_slots")
            tournament.total_slots = updates["total_slots"]
        if "entry_fee" in updates and updates["entry_fee"] is not None:
            tournament.entry_fee = updates["entry_fee"]
        if "prizes" in updates:
            tournament.prizes = updates["prizes"]
        if "rules" in updates:
            tournament.rules = updates["rules"]
        if "status" in updates and updates["status"] is not None:
            tournament.status = updates["status"]

        if tournament.end_time <= tournament.start_time:
            raise ValidationError("end_time must be after start_time")

        await self.session.commit()
        await self.session.refresh(tournament)
        return await self._to_response(tournament, owner_id)

    async def delete_tournament(self, tournament_id: UUID, owner_id: UUID) -> None:
        tournament = await self._get_owned_tournament(tournament_id, owner_id)
        await self.repo.delete(tournament)
        await self.session.commit()

    async def list_parlor_tournaments(
        self,
        parlor_id: UUID,
        *,
        status: str | None = None,
        upcoming: bool | None = None,
        viewer_id: UUID | None = None,
    ) -> list[TournamentResponse]:
        parlor = await self.parlor_repo.get_by_id(parlor_id)
        if parlor is None:
            raise NotFoundError("Parlor not found")

        tournaments = await self.repo.list_by_parlor(
            parlor_id,
            status=status,
            upcoming=upcoming,
        )
        return [await self._to_response(t, viewer_id) for t in tournaments]

    async def _get_owned_tournament(self, tournament_id: UUID, owner_id: UUID) -> Tournament:
        tournament = await self.repo.get_by_id(tournament_id)
        if tournament is None:
            raise NotFoundError("Tournament not found")

        if not await self.parlor_repo.is_owned_by(tournament.parlor_id, owner_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not own this tournament's parlor",
            )
        return tournament

    async def _to_response(
        self,
        tournament: Tournament,
        viewer_id: UUID | None,
    ) -> TournamentResponse:
        parlor = await self.parlor_repo.get_by_id(tournament.parlor_id)
        if parlor is None:
            raise NotFoundError("Parlor not found")

        is_booked_by_me = False
        if viewer_id is not None:
            is_booked_by_me = await self.repo.user_has_booking(tournament.id, viewer_id)

        return TournamentResponse(
            id=tournament.id,
            parlor_id=tournament.parlor_id,
            parlor=ParlorSummary(
                id=parlor.id,
                name=parlor.name,
                logo_url=parlor.logo_url,
                is_verified=parlor.is_verified,
            ),
            title=tournament.title,
            game_type=tournament.game_type,
            format=tournament.format,
            start_time=tournament.start_time,
            end_time=tournament.end_time,
            total_slots=tournament.total_slots,
            booked_slots=tournament.booked_slots,
            entry_fee=Decimal(str(tournament.entry_fee)),
            prizes=tournament.prizes,
            rules=tournament.rules,
            status=tournament.status,
            is_booked_by_me=is_booked_by_me,
            created_at=tournament.created_at,
            updated_at=tournament.updated_at,
        )