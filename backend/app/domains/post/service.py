"""Post domain business logic."""

import json
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.exceptions import NotFoundError, ValidationError
from app.domains.like.repository import LikeRepository
from app.domains.parlor.repository import ParlorRepository
from app.domains.parlor.schemas import ParlorSummary
from app.domains.post.models import Post
from app.domains.post.repository import PostRepository
from app.domains.post.schemas import PostCreate, PostResponse, TournamentPostSummary
from app.domains.tournament.repository import TournamentRepository
from app.domains.user.models import UserRole


class PostService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = PostRepository(session)
        self.parlor_repo = ParlorRepository(session)
        self.tournament_repo = TournamentRepository(session)
        self.like_repo = LikeRepository(session)

    async def create_post(
        self,
        owner_id: UUID,
        data: PostCreate,
        redis: aioredis.Redis | None = None,
        *,
        user_role: str | None = None,
    ) -> PostResponse:
        if user_role != UserRole.PARLOR_OWNER.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner only")

        parlor = (
            await self.parlor_repo.get_by_id(data.parlor_id)
            if data.parlor_id
            else await self.parlor_repo.get_by_owner_id(owner_id)
        )
        if parlor is None or parlor.owner_id != owner_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid parlor")

        if data.tournament_id:
            tournament = await self.tournament_repo.get_by_id(data.tournament_id)
            if tournament is None or tournament.parlor_id != parlor.id:
                raise ValidationError("Tournament does not belong to this parlor")

        post = Post(
            parlor_id=parlor.id,
            tournament_id=data.tournament_id,
            content=data.content.strip(),
            media_urls=data.media_urls,
        )
        created = await self.repo.create(post)
        await self.parlor_repo.increment_post_count(parlor.id, 1)
        await self.session.commit()
        await self.session.refresh(created)

        response = await self._to_response(created, owner_id)
        if redis is not None:
            await self._invalidate_feed_cache(redis, owner_id)
            try:
                from sqlalchemy import select

                from app.domains.follow.models import Follow
                from app.ws.events import publish_event

                followers = await self.session.execute(
                    select(Follow.user_id).where(Follow.parlor_id == parlor.id)
                )
                payload = response.model_dump(mode="json")
                for (follower_id,) in followers.all():
                    await publish_event(
                        redis,
                        f"user:{follower_id}",
                        "new_post",
                        payload,
                    )
            except Exception:
                pass
        return response

    async def get_post(self, post_id: UUID, viewer_id: UUID | None = None) -> PostResponse:
        post = await self.repo.get_by_id(post_id)
        if post is None:
            raise NotFoundError("Post not found")
        return await self._to_response(post, viewer_id)

    async def delete_post(self, post_id: UUID, owner_id: UUID) -> None:
        post = await self.repo.get_by_id(post_id)
        if post is None:
            raise NotFoundError("Post not found")
        if not await self.parlor_repo.is_owned_by(post.parlor_id, owner_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner only")

        await self.repo.delete_cascade(post_id)
        await self.parlor_repo.increment_post_count(post.parlor_id, -1)
        await self.session.commit()

    async def list_parlor_posts(
        self,
        parlor_id: UUID,
        *,
        limit: int = 20,
        offset: int = 0,
        viewer_id: UUID | None = None,
    ) -> list[PostResponse]:
        if await self.parlor_repo.get_by_id(parlor_id) is None:
            raise NotFoundError("Parlor not found")
        posts = await self.repo.list_by_parlor(parlor_id, limit=limit, offset=offset)
        return [await self._to_response(p, viewer_id) for p in posts]

    async def _to_response(self, post: Post, viewer_id: UUID | None) -> PostResponse:
        parlor = await self.parlor_repo.get_by_id(post.parlor_id)
        if parlor is None:
            raise NotFoundError("Parlor not found")

        tournament_summary = None
        if post.tournament_id:
            tournament = await self.tournament_repo.get_by_id(post.tournament_id)
            if tournament:
                tournament_summary = TournamentPostSummary(id=tournament.id, title=tournament.title)

        is_liked = False
        if viewer_id:
            is_liked = await self.like_repo.exists(viewer_id, "post", post.id)

        return PostResponse(
            id=post.id,
            content=post.content,
            media_urls=post.media_urls or [],
            parlor=ParlorSummary(
                id=parlor.id,
                name=parlor.name,
                logo_url=parlor.logo_url,
                is_verified=parlor.is_verified,
            ),
            tournament=tournament_summary,
            likes_count=post.likes_count,
            comments_count=post.comments_count,
            is_liked=is_liked,
            created_at=post.created_at,
        )

    @staticmethod
    async def _invalidate_feed_cache(redis: aioredis.Redis, _user_id: UUID) -> None:
        async for key in redis.scan_iter(match="feed:*"):
            await redis.delete(key)