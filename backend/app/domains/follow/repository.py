"""Follow domain data access layer."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.follow.models import Follow
from app.domains.gaming_place.mappers import GamingPlaceView, to_view
from app.domains.gaming_place.models import GamingPlace, GamingPlaceExtension


class FollowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def exists(self, user_id: UUID, parlor_id: UUID) -> bool:
        result = await self.session.execute(
            select(Follow.id).where(Follow.user_id == user_id, Follow.parlor_id == parlor_id)
        )
        return result.scalar_one_or_none() is not None

    async def create(self, user_id: UUID, parlor_id: UUID) -> Follow | None:
        if await self.exists(user_id, parlor_id):
            return None
        follow = Follow(user_id=user_id, parlor_id=parlor_id)
        self.session.add(follow)
        await self.session.flush()
        await self.session.refresh(follow)
        return follow

    async def delete(self, user_id: UUID, parlor_id: UUID) -> bool:
        result = await self.session.execute(
            delete(Follow)
            .where(Follow.user_id == user_id, Follow.parlor_id == parlor_id)
            .returning(Follow.id)
        )
        return result.scalar_one_or_none() is not None

    async def list_follower_user_ids(self, parlor_id: UUID) -> list[UUID]:
        result = await self.session.execute(
            select(Follow.user_id).where(Follow.parlor_id == parlor_id)
        )
        return list(result.scalars().all())

    async def list_followed_parlors(self, user_id: UUID) -> list[GamingPlaceView]:
        result = await self.session.execute(
            select(GamingPlace, GamingPlaceExtension)
            .join(Follow, Follow.parlor_id == GamingPlace.id)
            .outerjoin(
                GamingPlaceExtension,
                GamingPlaceExtension.gaming_place_id == GamingPlace.id,
            )
            .where(Follow.user_id == user_id)
            .order_by(GamingPlace.name.asc())
        )
        views: list[GamingPlaceView] = []
        for place, ext in result.all():
            views.append(to_view(place, ext))
        return views