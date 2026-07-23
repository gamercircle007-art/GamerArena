"""Parlor domain business logic — backed by ``gaming_places``."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.exceptions import NotFoundError, ValidationError
from app.domains.follow.service import FollowService
from app.domains.gaming_place.mappers import GamingPlaceView
from app.domains.parlor.repository import ParlorRepository
from app.domains.parlor.schemas import (
    ParlorAnalyticsResponse,
    ParlorCreate,
    ParlorResponse,
    ParlorUpdate,
    TournamentBookingStat,
)
from app.domains.post.models import Post
from app.domains.tournament.models import Booking, Tournament
from app.domains.user.models import UserRole


class ParlorService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ParlorRepository(session)
        self.follow_service = FollowService(session)

    async def create_parlor(
        self,
        owner_id: UUID,
        data: ParlorCreate,
        *,
        user_role: str | None = None,
    ) -> ParlorResponse:
        if user_role != UserRole.PARLOR_OWNER.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner only")
        if await self.repo.get_by_owner_id(owner_id):
            raise ValidationError("Parlor already exists for this owner")
        raise ValidationError(
            "Gaming venues are managed via the gaming_places catalog. "
            "Claim an existing venue instead of creating a new one."
        )

    async def get_parlor(self, parlor_id: UUID, viewer_id: UUID | None = None) -> ParlorResponse:
        parlor = await self.repo.get_by_id(parlor_id)
        if parlor is None:
            raise NotFoundError("Parlor not found")
        return await self._to_response(parlor, viewer_id)

    async def update_parlor(
        self,
        parlor_id: UUID,
        owner_id: UUID,
        data: ParlorUpdate,
    ) -> ParlorResponse:
        if not await self.repo.is_owned_by(parlor_id, owner_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner only")
        raise ValidationError("Venue details are synced from gaming_places and cannot be edited here")

    async def get_owner_analytics(self, owner_id: UUID) -> ParlorAnalyticsResponse:
        parlor = await self.repo.get_by_owner_id(owner_id)
        if parlor is None:
            raise NotFoundError("Parlor not found")

        now = datetime.now(UTC)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        upcoming_result = await self.session.execute(
            select(func.count())
            .select_from(Tournament)
            .where(
                Tournament.parlor_id == parlor.id,
                Tournament.start_time > now,
            )
        )
        upcoming_count = int(upcoming_result.scalar_one())

        posts_result = await self.session.execute(
            select(func.count()).select_from(Post).where(Post.parlor_id == parlor.id)
        )
        total_posts = int(posts_result.scalar_one())

        bookings_month_result = await self.session.execute(
            select(func.count())
            .select_from(Booking)
            .join(Tournament, Booking.tournament_id == Tournament.id)
            .where(
                Tournament.parlor_id == parlor.id,
                Booking.status != "cancelled",
                Booking.created_at >= month_start,
            )
        )
        bookings_month = int(bookings_month_result.scalar_one())

        stats_result = await self.session.execute(
            select(Tournament.id, Tournament.title, func.count(Booking.id))
            .join(Booking, Booking.tournament_id == Tournament.id, isouter=True)
            .where(Tournament.parlor_id == parlor.id, Booking.status != "cancelled")
            .group_by(Tournament.id, Tournament.title)
            .order_by(func.count(Booking.id).desc())
            .limit(10)
        )
        bookings_by_tournament = [
            TournamentBookingStat(
                tournament_id=row[0],
                title=row[1],
                bookings_count=int(row[2] or 0),
            )
            for row in stats_result.all()
        ]

        return ParlorAnalyticsResponse(
            follower_count=parlor.follower_count,
            total_posts=total_posts,
            upcoming_tournaments_count=upcoming_count,
            total_bookings_this_month=bookings_month,
            bookings_by_tournament=bookings_by_tournament,
        )

    async def _to_response(
        self,
        parlor: GamingPlaceView,
        viewer_id: UUID | None,
    ) -> ParlorResponse:
        is_following = await self.follow_service.is_following(viewer_id, parlor.id)
        return ParlorResponse(
            id=parlor.id,
            owner_id=parlor.owner_id,
            name=parlor.name,
            description=parlor.description,
            logo_url=parlor.logo_url,
            address=parlor.address,
            game_types=parlor.game_types,
            is_verified=parlor.is_verified,
            follower_count=parlor.follower_count,
            post_count=parlor.post_count,
            is_following=is_following,
            rating=parlor.rating,
            phone=parlor.phone,
            website=parlor.website,
            latitude=parlor.latitude,
            longitude=parlor.longitude,
            is_active=parlor.is_active,
            is_deleted=parlor.is_deleted,
            created_at=parlor.created_at,
            updated_at=parlor.updated_at,
        )