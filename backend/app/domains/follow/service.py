"""Follow domain business logic."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.exceptions import NotFoundError
from app.domains.follow.repository import FollowRepository
from app.domains.parlor.repository import ParlorRepository
from app.domains.parlor.schemas import ParlorSummary


class FollowService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = FollowRepository(session)
        self.parlor_repo = ParlorRepository(session)

    async def follow(self, user_id: UUID, parlor_id: UUID) -> None:
        if await self.parlor_repo.get_by_id(parlor_id) is None:
            raise NotFoundError("Parlor not found")
        created = await self.repo.create(user_id, parlor_id)
        if created:
            await self.parlor_repo.increment_follower_count(parlor_id, 1)
        await self.session.commit()

    async def unfollow(self, user_id: UUID, parlor_id: UUID) -> None:
        if await self.parlor_repo.get_by_id(parlor_id) is None:
            raise NotFoundError("Parlor not found")
        removed = await self.repo.delete(user_id, parlor_id)
        if removed:
            await self.parlor_repo.increment_follower_count(parlor_id, -1)
        await self.session.commit()

    async def list_following(self, user_id: UUID) -> list[ParlorSummary]:
        parlors = await self.repo.list_followed_parlors(user_id)
        return [
            ParlorSummary(
                id=p.id,
                name=p.name,
                logo_url=p.logo_url,
                is_verified=p.is_verified,
            )
            for p in parlors
        ]

    async def is_following(self, user_id: UUID | None, parlor_id: UUID) -> bool:
        if user_id is None:
            return False
        return await self.repo.exists(user_id, parlor_id)