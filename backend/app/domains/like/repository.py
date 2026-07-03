"""Like domain data access layer."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.like.models import Like


class LikeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def exists(self, user_id: UUID, target_type: str, target_id: UUID) -> bool:
        result = await self.session.execute(
            select(Like.id).where(
                Like.user_id == user_id,
                Like.target_type == target_type,
                Like.target_id == target_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def add(self, user_id: UUID, target_type: str, target_id: UUID) -> bool:
        stmt = (
            insert(Like)
            .values(user_id=user_id, target_type=target_type, target_id=target_id)
            .on_conflict_do_nothing(constraint="uq_likes_user_target")
            .returning(Like.id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def remove(self, user_id: UUID, target_type: str, target_id: UUID) -> bool:
        result = await self.session.execute(
            delete(Like)
            .where(
                Like.user_id == user_id,
                Like.target_type == target_type,
                Like.target_id == target_id,
            )
            .returning(Like.id)
        )
        return result.scalar_one_or_none() is not None