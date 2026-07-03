"""Like domain business logic."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.comment.models import Comment
from app.domains.common.exceptions import NotFoundError, ValidationError
from app.domains.like.repository import LikeRepository
from app.domains.like.schemas import LikeToggleResponse
from app.domains.post.models import Post
from app.domains.reel.models import Reel, ReelComment


class LikeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = LikeRepository(session)

    async def add_like(
        self,
        user_id: UUID,
        target_type: str,
        target_id: UUID,
    ) -> LikeToggleResponse:
        target = await self._get_target(target_type, target_id)
        inserted = await self.repo.add(user_id, target_type, target_id)
        if inserted:
            target.likes_count += 1
        await self.session.commit()
        await self.session.refresh(target)
        return LikeToggleResponse(liked=True, likes_count=target.likes_count)

    async def remove_like(
        self,
        user_id: UUID,
        target_type: str,
        target_id: UUID,
    ) -> LikeToggleResponse:
        target = await self._get_target(target_type, target_id)
        removed = await self.repo.remove(user_id, target_type, target_id)
        if removed and target.likes_count > 0:
            target.likes_count -= 1
        await self.session.commit()
        await self.session.refresh(target)
        return LikeToggleResponse(liked=False, likes_count=target.likes_count)

    async def toggle_comment_like(self, user_id: UUID, comment_id: UUID) -> LikeToggleResponse:
        if await self.repo.exists(user_id, "comment", comment_id):
            return await self.remove_like(user_id, "comment", comment_id)
        return await self.add_like(user_id, "comment", comment_id)

    async def _get_target(
        self, target_type: str, target_id: UUID
    ) -> Post | Comment | Reel | ReelComment:
        if target_type == "post":
            result = await self.session.get(Post, target_id)
            if result is None:
                raise NotFoundError("Post not found")
            return result
        if target_type == "comment":
            result = await self.session.get(Comment, target_id)
            if result is None:
                raise NotFoundError("Comment not found")
            return result
        if target_type == "reel":
            result = await self.session.get(Reel, target_id)
            if result is None or result.is_deleted:
                raise NotFoundError("Reel not found")
            return result
        if target_type == "reel_comment":
            result = await self.session.get(ReelComment, target_id)
            if result is None or result.is_deleted:
                raise NotFoundError("Comment not found")
            return result
        raise ValidationError("Invalid target_type")