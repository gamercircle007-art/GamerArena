"""Reel data access."""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.reel.models import (
    Reel,
    ReelBookmark,
    ReelComment,
    ReelReport,
    ReelView,
    UserFollow,
)
from app.domains.user.models import User


class ReelRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, reel: Reel) -> Reel:
        self.session.add(reel)
        await self.session.flush()
        return reel

    async def get_by_id(self, reel_id: UUID) -> Reel | None:
        result = await self.session.execute(
            select(Reel).where(Reel.id == reel_id, Reel.is_deleted.is_(False))
        )
        return result.scalar_one_or_none()

    async def soft_delete(self, reel: Reel) -> Reel:
        reel.is_deleted = True
        await self.session.flush()
        return reel

    async def list_feed(
        self,
        *,
        viewer_id: UUID | None,
        page: int,
        limit: int,
        sort: str = "trending",
    ) -> list[Reel]:
        offset = (page - 1) * limit
        stmt = select(Reel).where(Reel.is_deleted.is_(False))

        if viewer_id is not None:
            following_subq = select(UserFollow.following_id).where(
                UserFollow.follower_id == viewer_id
            )
            stmt = stmt.where(
                or_(
                    Reel.privacy == "public",
                    Reel.privacy == "international",
                    Reel.privacy == "unlisted",
                    (Reel.user_id == viewer_id),
                    (Reel.privacy == "followers") & (Reel.user_id.in_(following_subq)),
                )
            )
        else:
            stmt = stmt.where(Reel.privacy.in_(["public", "international", "unlisted"]))

        if sort == "newest":
            stmt = stmt.order_by(Reel.created_at.desc())
        elif sort == "popular":
            stmt = stmt.order_by(Reel.likes_count.desc(), Reel.views_count.desc())
        else:
            stmt = stmt.order_by(
                (Reel.likes_count * 2 + Reel.views_count + Reel.comments_count).desc(),
                Reel.created_at.desc(),
            )

        result = await self.session.execute(stmt.offset(offset).limit(limit))
        return list(result.scalars().all())

    async def search(
        self,
        *,
        q: str,
        viewer_id: UUID | None,
        page: int,
        limit: int,
        sort: str = "trending",
    ) -> list[Reel]:
        needle = f"%{q.strip().lower()}%"
        offset = (page - 1) * limit
        stmt = (
            select(Reel)
            .where(Reel.is_deleted.is_(False))
            .join(User, User.id == Reel.user_id)
            .where(
                or_(
                    func.lower(Reel.caption).like(needle),
                    func.lower(Reel.location).like(needle),
                    func.lower(User.username).like(needle),
                    func.lower(User.full_name).like(needle),
                )
            )
        )
        if viewer_id is None:
            stmt = stmt.where(Reel.privacy.in_(["public", "international", "unlisted"]))
        if sort == "newest":
            stmt = stmt.order_by(Reel.created_at.desc())
        else:
            stmt = stmt.order_by(Reel.likes_count.desc(), Reel.views_count.desc())
        result = await self.session.execute(stmt.offset(offset).limit(limit))
        return list(result.scalars().all())

    async def list_by_user(self, user_id: UUID, *, page: int, limit: int) -> list[Reel]:
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(Reel)
            .where(Reel.user_id == user_id, Reel.is_deleted.is_(False))
            .order_by(Reel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def add_view(self, reel_id: UUID, user_id: UUID | None) -> None:
        self.session.add(ReelView(reel_id=reel_id, user_id=user_id))

    async def toggle_bookmark(self, user_id: UUID, reel_id: UUID) -> tuple[bool, bool]:
        result = await self.session.execute(
            select(ReelBookmark).where(
                ReelBookmark.user_id == user_id,
                ReelBookmark.reel_id == reel_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            await self.session.delete(existing)
            return False, True
        self.session.add(ReelBookmark(user_id=user_id, reel_id=reel_id))
        return True, False

    async def is_bookmarked(self, user_id: UUID, reel_id: UUID) -> bool:
        result = await self.session.execute(
            select(ReelBookmark.id).where(
                ReelBookmark.user_id == user_id,
                ReelBookmark.reel_id == reel_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def add_comment(self, comment: ReelComment) -> ReelComment:
        self.session.add(comment)
        await self.session.flush()
        return comment

    async def get_comment(self, comment_id: UUID) -> ReelComment | None:
        return await self.session.get(ReelComment, comment_id)

    async def list_comments(
        self, reel_id: UUID, *, limit: int, after_id: UUID | None
    ) -> list[ReelComment]:
        stmt = (
            select(ReelComment)
            .where(
                ReelComment.reel_id == reel_id,
                ReelComment.parent_id.is_(None),
                ReelComment.is_deleted.is_(False),
            )
            .order_by(ReelComment.is_pinned.desc(), ReelComment.created_at.desc())
            .limit(limit)
        )
        if after_id:
            after = await self.get_comment(after_id)
            if after:
                stmt = stmt.where(ReelComment.created_at < after.created_at)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_replies(self, parent_id: UUID, *, limit: int, page: int) -> list[ReelComment]:
        offset = (page - 1) * limit
        result = await self.session.execute(
            select(ReelComment)
            .where(
                ReelComment.parent_id == parent_id,
                ReelComment.is_deleted.is_(False),
            )
            .order_by(ReelComment.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def reply_count(self, comment_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ReelComment)
            .where(ReelComment.parent_id == comment_id, ReelComment.is_deleted.is_(False))
        )
        return int(result.scalar_one())

    async def soft_delete_comment(self, comment: ReelComment) -> ReelComment:
        comment.is_deleted = True
        comment.content = "[deleted]"
        await self.session.flush()
        return comment

    async def add_report(self, report: ReelReport) -> ReelReport:
        self.session.add(report)
        await self.session.flush()
        return report

    async def add_follow(self, follower_id: UUID, following_id: UUID) -> bool:
        if await self.is_following(follower_id, following_id):
            return False
        self.session.add(UserFollow(follower_id=follower_id, following_id=following_id))
        return True

    async def remove_follow(self, follower_id: UUID, following_id: UUID) -> bool:
        result = await self.session.execute(
            select(UserFollow).where(
                UserFollow.follower_id == follower_id,
                UserFollow.following_id == following_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            return False
        await self.session.delete(existing)
        return True

    async def is_following(self, follower_id: UUID, following_id: UUID) -> bool:
        result = await self.session.execute(
            select(UserFollow.id).where(
                UserFollow.follower_id == follower_id,
                UserFollow.following_id == following_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def followers_count(self, user_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(UserFollow).where(UserFollow.following_id == user_id)
        )
        return int(result.scalar_one())

    async def following_count(self, user_id: UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(UserFollow).where(UserFollow.follower_id == user_id)
        )
        return int(result.scalar_one())