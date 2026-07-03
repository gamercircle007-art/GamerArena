"""Comment domain business logic."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.comment.models import Comment
from app.domains.comment.repository import CommentRepository
from app.domains.comment.schemas import CommentCreate, CommentResponse, CommentUserSummary
from app.domains.common.exceptions import NotFoundError, ValidationError
from app.domains.like.repository import LikeRepository
from app.domains.parlor.repository import ParlorRepository
from app.domains.post.models import Post
from app.domains.user.repository import UserRepository

REMOVED_CONTENT = "[Comment removed]"


class CommentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CommentRepository(session)
        self.post_model = Post
        self.user_repo = UserRepository(session)
        self.parlor_repo = ParlorRepository(session)
        self.like_repo = LikeRepository(session)

    async def list_post_comments(
        self,
        post_id: UUID,
        *,
        limit: int = 20,
        after_id: UUID | None = None,
        viewer_id: UUID | None = None,
    ) -> list[CommentResponse]:
        await self._get_post_or_404(post_id)
        comments = await self.repo.list_top_level(post_id, limit=limit, after_id=after_id)
        return [await self._to_response(c, viewer_id) for c in comments]

    async def add_comment(
        self,
        post_id: UUID,
        user_id: UUID,
        data: CommentCreate,
        redis=None,
    ) -> CommentResponse:
        post = await self._get_post_or_404(post_id)
        if data.parent_id:
            parent = await self.repo.get_by_id(data.parent_id)
            if parent is None or parent.post_id != post_id:
                raise ValidationError("Invalid parent comment")

        comment = Comment(
            post_id=post_id,
            user_id=user_id,
            parent_id=data.parent_id,
            content=data.content.strip(),
        )
        created = await self.repo.create(comment)
        post.comments_count += 1
        await self.session.commit()
        await self.session.refresh(created)
        response = await self._to_response(created, user_id)
        if redis is not None:
            try:
                from app.ws.events import publish_event

                await publish_event(
                    redis,
                    f"post:comments:{post_id}",
                    "new_comment",
                    response.model_dump(mode="json"),
                )
            except Exception:
                pass
        return response

    async def list_replies(
        self,
        comment_id: UUID,
        *,
        limit: int = 10,
        page: int = 1,
        viewer_id: UUID | None = None,
    ) -> list[CommentResponse]:
        if await self.repo.get_by_id(comment_id) is None:
            raise NotFoundError("Comment not found")
        replies = await self.repo.list_replies(comment_id, limit=limit, page=page)
        return [await self._to_response(r, viewer_id) for r in replies]

    async def soft_delete(self, comment_id: UUID, user_id: UUID) -> CommentResponse:
        comment = await self.repo.get_by_id(comment_id)
        if comment is None:
            raise NotFoundError("Comment not found")

        post = await self._get_post_or_404(comment.post_id)
        is_owner = comment.user_id == user_id
        is_parlor_owner = await self.parlor_repo.is_owned_by(post.parlor_id, user_id)
        if not is_owner and not is_parlor_owner:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

        if not comment.is_deleted:
            comment.is_deleted = True
            comment.content = REMOVED_CONTENT
            await self.session.commit()
            await self.session.refresh(comment)
        return await self._to_response(comment, user_id)

    async def _get_post_or_404(self, post_id: UUID) -> Post:
        post = await self.session.get(Post, post_id)
        if post is None:
            raise NotFoundError("Post not found")
        return post

    async def _to_response(self, comment: Comment, viewer_id: UUID | None) -> CommentResponse:
        user = await self.user_repo.get_by_id(comment.user_id)
        if user is None:
            raise NotFoundError("User not found")

        is_liked = False
        if viewer_id:
            is_liked = await self.like_repo.exists(viewer_id, "comment", comment.id)

        reply_count = 0
        if comment.parent_id is None:
            reply_count = await self.repo.reply_count(comment.id)

        content = REMOVED_CONTENT if comment.is_deleted else comment.content
        return CommentResponse(
            id=comment.id,
            user=CommentUserSummary.model_validate(user),
            content=content,
            parent_id=comment.parent_id,
            likes_count=comment.likes_count,
            is_liked=is_liked,
            is_deleted=comment.is_deleted,
            reply_count=reply_count,
            created_at=comment.created_at,
        )