"""Post domain data access layer."""

from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.comment.models import Comment
from app.domains.follow.models import Follow
from app.domains.gaming_place.models import GamingPlace
from app.domains.like.models import Like
from app.domains.post.models import Post


class PostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, post_id: UUID) -> Post | None:
        result = await self.session.execute(select(Post).where(Post.id == post_id))
        return result.scalar_one_or_none()

    async def list_by_parlor(self, parlor_id: UUID, *, limit: int = 20, offset: int = 0) -> list[Post]:
        result = await self.session.execute(
            select(Post)
            .where(Post.parlor_id == parlor_id)
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_recent(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        city: str | None = None,
    ) -> list[Post]:
        stmt = select(Post)
        if city:
            needle = city.strip().lower()
            stmt = (
                select(Post)
                .join(GamingPlace, GamingPlace.id == Post.parlor_id)
                .where(
                    func.lower(GamingPlace.address).contains(needle)
                    | func.lower(GamingPlace.name).contains(needle)
                )
            )
        stmt = stmt.order_by(Post.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_from_followed(self, user_id: UUID, *, limit: int, offset: int) -> list[Post]:
        result = await self.session.execute(
            select(Post)
            .join(Follow, Follow.parlor_id == Post.parlor_id)
            .where(Follow.user_id == user_id)
            .order_by(Post.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, post: Post) -> Post:
        self.session.add(post)
        await self.session.flush()
        await self.session.refresh(post)
        return post

    async def delete_cascade(self, post_id: UUID) -> None:
        comment_ids = await self.session.execute(
            select(Comment.id).where(Comment.post_id == post_id)
        )
        ids = [row[0] for row in comment_ids.all()]
        targets = [post_id, *ids]
        await self.session.execute(
            delete(Like).where(
                Like.target_id.in_(targets),
                Like.target_type.in_(["post", "comment"]),
            )
        )
        await self.session.execute(delete(Comment).where(Comment.post_id == post_id))
        await self.session.execute(delete(Post).where(Post.id == post_id))
        await self.session.flush()