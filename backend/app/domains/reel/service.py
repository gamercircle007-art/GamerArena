"""Reel domain business logic."""

import re
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.domains.common.exceptions import NotFoundError, ValidationError
from app.domains.like.repository import LikeRepository
from app.domains.notification.service import NotificationService
from app.domains.reel.models import Reel, ReelComment, ReelPrivacy, ReelReport
from app.domains.reel.repository import ReelRepository
from app.domains.reel.schemas import (
    DemoMusicTrack,
    ReelBookmarkResponse,
    ReelCommentCreate,
    ReelCommentResponse,
    ReelCreate,
    ReelFeedResponse,
    ReelResponse,
    ReelShareResponse,
    ReelUpdate,
    ReelUserSummary,
    ReelViewResponse,
    UserFollowResponse,
)
from app.domains.user.models import User

_HASHTAG_RE = re.compile(r"#(\w+)", re.UNICODE)

DEMO_MUSIC = [
    DemoMusicTrack(
        id="beat1",
        title="Neon Pulse",
        artist="GamerCircle",
        preview_url="https://dev-cdn.example.com/music/neon-pulse.mp3",
    ),
    DemoMusicTrack(
        id="beat2",
        title="Arena Drop",
        artist="GamerCircle",
        preview_url="https://dev-cdn.example.com/music/arena-drop.mp3",
    ),
    DemoMusicTrack(
        id="beat3",
        title="Boss Fight",
        artist="GamerCircle",
        preview_url="https://dev-cdn.example.com/music/boss-fight.mp3",
    ),
]


class ReelService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ReelRepository(session)
        self.like_repo = LikeRepository(session)
        self.notifications = NotificationService(session)

    def _extract_hashtags(self, caption: str | None, extra: list[str]) -> list[str]:
        tags = {t.lower() for t in extra if t}
        if caption:
            tags.update(m.group(1).lower() for m in _HASHTAG_RE.finditer(caption))
        return sorted(tags)[:30]

    async def _user_summary(
        self, user: User, viewer_id: UUID | None = None
    ) -> ReelUserSummary:
        followers = await self.repo.followers_count(user.id)
        following = await self.repo.following_count(user.id)
        is_following = (
            await self.repo.is_following(viewer_id, user.id)
            if viewer_id and viewer_id != user.id
            else False
        )
        return ReelUserSummary(
            id=user.id,
            username=user.username,
            name=user.full_name,
            avatar_url=user.avatar_url,
            followers_count=followers,
            following_count=following,
            is_following=is_following,
        )

    async def _to_response(
        self, reel: Reel, viewer_id: UUID | None = None
    ) -> ReelResponse:
        user = await self.session.get(User, reel.user_id)
        if user is None:
            raise NotFoundError("Creator not found")
        is_liked = (
            await self.like_repo.exists(viewer_id, "reel", reel.id)
            if viewer_id
            else False
        )
        is_bookmarked = (
            await self.repo.is_bookmarked(viewer_id, reel.id) if viewer_id else False
        )
        return ReelResponse(
            id=reel.id,
            user=await self._user_summary(user, viewer_id),
            video_url=reel.video_url,
            thumbnail_url=reel.thumbnail_url,
            cover_url=reel.cover_url,
            caption=reel.caption,
            hashtags=reel.hashtags or [],
            location=reel.location,
            duration_seconds=reel.duration_seconds,
            width=reel.width,
            height=reel.height,
            aspect_ratio=reel.aspect_ratio,
            filter_name=reel.filter_name,
            music_title=reel.music_title,
            music_url=reel.music_url,
            privacy=reel.privacy,
            likes_count=reel.likes_count,
            comments_count=reel.comments_count,
            views_count=reel.views_count,
            shares_count=reel.shares_count,
            bookmarks_count=reel.bookmarks_count,
            is_liked=is_liked,
            is_bookmarked=is_bookmarked,
            created_at=reel.created_at,
        )

    async def create_reel(self, user_id: UUID, data: ReelCreate) -> ReelResponse:
        if data.duration_seconds is not None and not (5 <= data.duration_seconds <= 30):
            raise ValidationError("Reel duration must be between 5 and 30 seconds")
        hashtags = self._extract_hashtags(data.caption, data.hashtags)
        reel = Reel(
            user_id=user_id,
            video_url=data.video_url,
            thumbnail_url=data.thumbnail_url,
            cover_url=data.cover_url or data.thumbnail_url,
            caption=data.caption,
            hashtags=hashtags,
            location=data.location,
            duration_seconds=data.duration_seconds,
            width=data.width,
            height=data.height,
            aspect_ratio=data.aspect_ratio,
            filter_name=data.filter_name,
            music_title=data.music_title,
            music_url=data.music_url,
            privacy=data.privacy.value,
        )
        created = await self.repo.create(reel)
        await self.session.commit()
        await self.session.refresh(created)
        return await self._to_response(created, user_id)

    async def get_reel(self, reel_id: UUID, viewer_id: UUID | None = None) -> ReelResponse:
        reel = await self.repo.get_by_id(reel_id)
        if reel is None:
            raise NotFoundError("Reel not found")
        if reel.privacy == ReelPrivacy.PRIVATE.value and viewer_id != reel.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Private reel")
        return await self._to_response(reel, viewer_id)

    async def feed(
        self,
        *,
        viewer_id: UUID | None,
        page: int = 1,
        limit: int = 10,
        sort: str = "trending",
    ) -> ReelFeedResponse:
        limit = min(max(limit, 1), 30)
        reels = await self.repo.list_feed(
            viewer_id=viewer_id, page=page, limit=limit + 1, sort=sort
        )
        has_more = len(reels) > limit
        items = reels[:limit]
        responses = [await self._to_response(r, viewer_id) for r in items]
        return ReelFeedResponse(
            items=responses, page=page, limit=limit, has_more=has_more
        )

    async def search_reels(
        self,
        q: str,
        *,
        viewer_id: UUID | None,
        page: int = 1,
        limit: int = 20,
        sort: str = "trending",
    ) -> ReelFeedResponse:
        if not q.strip():
            return await self.feed(viewer_id=viewer_id, page=page, limit=limit, sort=sort)
        limit = min(max(limit, 1), 30)
        reels = await self.repo.search(
            q=q, viewer_id=viewer_id, page=page, limit=limit + 1, sort=sort
        )
        has_more = len(reels) > limit
        items = reels[:limit]
        responses = [await self._to_response(r, viewer_id) for r in items]
        return ReelFeedResponse(
            items=responses, page=page, limit=limit, has_more=has_more
        )

    async def record_view(
        self, reel_id: UUID, viewer_id: UUID | None
    ) -> ReelViewResponse:
        reel = await self.repo.get_by_id(reel_id)
        if reel is None:
            raise NotFoundError("Reel not found")
        await self.repo.add_view(reel_id, viewer_id)
        reel.views_count += 1
        await self.session.commit()
        await self.session.refresh(reel)
        return ReelViewResponse(views_count=reel.views_count)

    async def toggle_bookmark(
        self, user_id: UUID, reel_id: UUID
    ) -> ReelBookmarkResponse:
        reel = await self.repo.get_by_id(reel_id)
        if reel is None:
            raise NotFoundError("Reel not found")
        added, removed = await self.repo.toggle_bookmark(user_id, reel_id)
        if added:
            reel.bookmarks_count += 1
        elif removed and reel.bookmarks_count > 0:
            reel.bookmarks_count -= 1
        await self.session.commit()
        await self.session.refresh(reel)
        return ReelBookmarkResponse(
            bookmarked=added,
            bookmarks_count=reel.bookmarks_count,
        )

    async def record_share(self, reel_id: UUID) -> ReelShareResponse:
        reel = await self.repo.get_by_id(reel_id)
        if reel is None:
            raise NotFoundError("Reel not found")
        reel.shares_count += 1
        await self.session.commit()
        await self.session.refresh(reel)
        settings = get_settings()
        share_url = f"{settings.api_v1_prefix}/reels/{reel_id}"
        return ReelShareResponse(shares_count=reel.shares_count, share_url=share_url)

    async def delete_reel(self, user_id: UUID, reel_id: UUID) -> None:
        reel = await self.repo.get_by_id(reel_id)
        if reel is None:
            raise NotFoundError("Reel not found")
        if reel.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your reel")
        await self.repo.soft_delete(reel)
        await self.session.commit()

    async def update_reel(
        self, user_id: UUID, reel_id: UUID, data: ReelUpdate
    ) -> ReelResponse:
        reel = await self.repo.get_by_id(reel_id)
        if reel is None:
            raise NotFoundError("Reel not found")
        if reel.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your reel")
        if data.caption is not None:
            reel.caption = data.caption
            reel.hashtags = self._extract_hashtags(data.caption, reel.hashtags or [])
        if data.privacy is not None:
            reel.privacy = data.privacy.value
        if data.cover_url is not None:
            reel.cover_url = data.cover_url
        await self.session.commit()
        await self.session.refresh(reel)
        return await self._to_response(reel, user_id)

    async def add_comment(
        self,
        reel_id: UUID,
        user_id: UUID,
        data: ReelCommentCreate,
        redis: aioredis.Redis | None = None,
    ) -> ReelCommentResponse:
        reel = await self.repo.get_by_id(reel_id)
        if reel is None:
            raise NotFoundError("Reel not found")
        if data.parent_id:
            parent = await self.repo.get_comment(data.parent_id)
            if parent is None or parent.reel_id != reel_id:
                raise ValidationError("Invalid parent comment")
        comment = ReelComment(
            reel_id=reel_id,
            user_id=user_id,
            parent_id=data.parent_id,
            content=data.content.strip(),
        )
        created = await self.repo.add_comment(comment)
        reel.comments_count += 1
        await self.session.commit()
        await self.session.refresh(created)

        if reel.user_id != user_id:
            await self.notifications.create_notification(
                user_id=reel.user_id,
                type="reel_comment",
                title="New comment on your reel",
                body=data.content[:120],
                data={"reel_id": str(reel_id), "comment_id": str(created.id)},
                redis=redis,
            )
        return await self._comment_response(created, user_id)

    async def _comment_response(
        self, comment: ReelComment, viewer_id: UUID | None
    ) -> ReelCommentResponse:
        user = await self.session.get(User, comment.user_id)
        if user is None:
            raise NotFoundError("User not found")
        is_liked = (
            await self.like_repo.exists(viewer_id, "reel_comment", comment.id)
            if viewer_id
            else False
        )
        reply_count = await self.repo.reply_count(comment.id)
        return ReelCommentResponse(
            id=comment.id,
            user=await self._user_summary(user, viewer_id),
            content=comment.content,
            parent_id=comment.parent_id,
            likes_count=comment.likes_count,
            is_liked=is_liked,
            is_pinned=comment.is_pinned,
            is_deleted=comment.is_deleted,
            reply_count=reply_count,
            created_at=comment.created_at,
        )

    async def list_comments(
        self,
        reel_id: UUID,
        *,
        viewer_id: UUID | None,
        limit: int = 20,
        after_id: UUID | None = None,
    ) -> list[ReelCommentResponse]:
        comments = await self.repo.list_comments(reel_id, limit=limit, after_id=after_id)
        return [await self._comment_response(c, viewer_id) for c in comments]

    async def list_replies(
        self,
        comment_id: UUID,
        *,
        viewer_id: UUID | None,
        limit: int = 10,
        page: int = 1,
    ) -> list[ReelCommentResponse]:
        comments = await self.repo.list_replies(comment_id, limit=limit, page=page)
        return [await self._comment_response(c, viewer_id) for c in comments]

    async def delete_comment(self, comment_id: UUID, user_id: UUID) -> ReelCommentResponse:
        comment = await self.repo.get_comment(comment_id)
        if comment is None:
            raise NotFoundError("Comment not found")
        if comment.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your comment")
        reel = await self.repo.get_by_id(comment.reel_id)
        if reel and reel.comments_count > 0:
            reel.comments_count -= 1
        updated = await self.repo.soft_delete_comment(comment)
        await self.session.commit()
        return await self._comment_response(updated, user_id)

    async def report_reel(
        self, reel_id: UUID, reporter_id: UUID, reason: str
    ) -> None:
        reel = await self.repo.get_by_id(reel_id)
        if reel is None:
            raise NotFoundError("Reel not found")
        await self.repo.add_report(
            ReelReport(reel_id=reel_id, reporter_id=reporter_id, reason=reason)
        )
        await self.session.commit()

    async def follow_user(
        self, follower_id: UUID, following_id: UUID, redis: aioredis.Redis | None = None
    ) -> UserFollowResponse:
        if follower_id == following_id:
            raise ValidationError("Cannot follow yourself")
        target = await self.session.get(User, following_id)
        if target is None:
            raise NotFoundError("User not found")
        added = await self.repo.add_follow(follower_id, following_id)
        await self.session.commit()
        if added:
            await self.notifications.create_notification(
                user_id=following_id,
                type="new_follower",
                title="New follower",
                body="Someone started following you",
                data={"follower_id": str(follower_id)},
                redis=redis,
            )
        followers = await self.repo.followers_count(following_id)
        return UserFollowResponse(following=True, followers_count=followers)

    async def unfollow_user(self, follower_id: UUID, following_id: UUID) -> UserFollowResponse:
        if follower_id == following_id:
            raise ValidationError("Cannot unfollow yourself")
        await self.repo.remove_follow(follower_id, following_id)
        await self.session.commit()
        followers = await self.repo.followers_count(following_id)
        return UserFollowResponse(following=False, followers_count=followers)

    async def demo_music(self) -> list[DemoMusicTrack]:
        return DEMO_MUSIC

    async def notify_like(
        self,
        reel_id: UUID,
        liker_id: UUID,
        redis: aioredis.Redis | None = None,
    ) -> None:
        reel = await self.repo.get_by_id(reel_id)
        if reel is None or reel.user_id == liker_id:
            return
        await self.notifications.create_notification(
            user_id=reel.user_id,
            type="reel_like",
            title="Reel liked",
            body="Someone liked your reel",
            data={"reel_id": str(reel_id), "liker_id": str(liker_id)},
            redis=redis,
        )