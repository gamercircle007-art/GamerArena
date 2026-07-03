"""Comment domain data access layer."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.comment.models import Comment


class CommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, comment_id: UUID) -> Comment | None:
        return await self.session.get(Comment, comment_id)

    async def list_top_level(
        self,
        post_id: UUID,
        *,
        limit: int = 20,
        after_id: UUID | None = None,
    ) -> list[Comment]:
        query = (
            select(Comment)
            .where(Comment.post_id == post_id, Comment.parent_id.is_(None))
            .order_by(Comment.created_at.asc())
            .limit(limit)
        )
        if after_id:
            anchor = await self.get_by_id(after_id)
            if anchor:
                query = query.where(Comment.created_at > anchor.created_at)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_replies(
        self,
        parent_id: UUID,
        *,
        limit: int = 10,
        page: int = 1,
    ) -> list[Comment]:
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(Comment)
            .where(Comment.parent_id == parent_id)
            .order_by(Comment.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def reply_count(self, comment_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Comment).where(Comment.parent_id == comment_id)
        )
        return int(result.scalar_one())

    async def create(self, comment: Comment) -> Comment:
        self.session.add(comment)
        await self.session.flush()
        await self.session.refresh(comment)
        return comment