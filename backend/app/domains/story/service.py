"""Stories business logic."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.exceptions import NotFoundError, ValidationError
from app.domains.common.social_notify import notify_user
from app.domains.friend.service import FriendService
from app.domains.story.models import Story, StoryView
from app.domains.story.schemas import StoryCreate, StoryGroupResponse, StoryResponse, StoryViewerResponse
from app.domains.user.repository import UserRepository
from app.ws.events import publish_to_user


class StoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.friend_service = FriendService(session)

    async def create_story(
        self, user_id: UUID, data: StoryCreate, redis: aioredis.Redis
    ) -> StoryResponse:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        story = Story(
            user_id=user_id,
            media_url=data.media_url,
            asset_id=data.asset_id,
            media_type=data.media_type,
            duration_seconds=data.duration_seconds,
            caption=data.caption,
            privacy=data.privacy,
            expires_at=expires_at,
        )
        self.session.add(story)
        await self.session.commit()
        await self.session.refresh(story)

        author = await self.user_repo.get_by_id(user_id)
        friend_ids = await self.friend_service._friend_ids(user_id)
        for fid in friend_ids:
            await publish_to_user(
                redis,
                fid,
                {
                    "type": "new_story",
                    "user_id": str(user_id),
                    "user_name": author.full_name if author else None,
                    "story_id": str(story.id),
                    "preview_url": story.media_url,
                },
            )
            await notify_user(
                self.session,
                redis,
                fid,
                type="new_story",
                title="New story",
                body=f"{author.full_name if author else 'A friend'} posted a story",
                data={"story_id": str(story.id), "user_id": str(user_id)},
                skip_if_online=True,
            )
        return StoryResponse.model_validate(story)

    async def get_feed(self, user_id: UUID) -> list[StoryGroupResponse]:
        friend_ids = await self.friend_service._friend_ids(user_id)
        all_ids = [user_id, *friend_ids]
        now = datetime.now(timezone.utc)

        result = await self.session.execute(
            select(Story, StoryView)
            .outerjoin(
                StoryView,
                and_(StoryView.story_id == Story.id, StoryView.viewer_id == user_id),
            )
            .where(Story.user_id.in_(all_ids), Story.expires_at > now)
            .order_by(Story.created_at.asc())
        )

        groups: dict[UUID, dict] = defaultdict(
            lambda: {"stories": [], "all_viewed": True, "user": None}
        )
        for story, view in result.all():
            gid = story.user_id
            if groups[gid]["user"] is None:
                user = await self.user_repo.get_by_id(gid)
                groups[gid]["user"] = user
            viewed = view is not None
            groups[gid]["stories"].append(
                StoryResponse.model_validate(story).model_copy(update={"viewed": viewed})
            )
            if not viewed and gid != user_id:
                groups[gid]["all_viewed"] = False

        feed: list[StoryGroupResponse] = []
        for gid, data in groups.items():
            user = data["user"]
            feed.append(
                StoryGroupResponse(
                    user_id=gid,
                    user_name=user.full_name if user else None,
                    user_avatar=user.avatar_url if user else None,
                    all_viewed=data["all_viewed"],
                    stories=data["stories"],
                )
            )
        return feed

    async def get_user_stories(self, target_id: UUID, viewer_id: UUID) -> list[StoryResponse]:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(Story, StoryView)
            .outerjoin(
                StoryView,
                and_(StoryView.story_id == Story.id, StoryView.viewer_id == viewer_id),
            )
            .where(Story.user_id == target_id, Story.expires_at > now)
            .order_by(Story.created_at.asc())
        )
        return [
            StoryResponse.model_validate(story).model_copy(update={"viewed": view is not None})
            for story, view in result.all()
        ]

    async def mark_viewed(self, story_id: UUID, viewer_id: UUID) -> None:
        story = await self.session.get(Story, story_id)
        if story is None:
            raise NotFoundError("Story not found")
        existing = await self.session.execute(
            select(StoryView).where(
                StoryView.story_id == story_id, StoryView.viewer_id == viewer_id
            )
        )
        if existing.scalar_one_or_none() is None:
            self.session.add(
                StoryView(
                    story_id=story_id,
                    viewer_id=viewer_id,
                    viewed_at=datetime.now(timezone.utc),
                )
            )
            story.view_count += 1
            await self.session.commit()

    async def get_viewers(self, story_id: UUID, owner_id: UUID) -> list[StoryViewerResponse]:
        story = await self.session.get(Story, story_id)
        if story is None or story.user_id != owner_id:
            raise ValidationError("Not authorized")
        result = await self.session.execute(
            select(StoryView).where(StoryView.story_id == story_id).order_by(StoryView.viewed_at.desc())
        )
        viewers: list[StoryViewerResponse] = []
        for view in result.scalars().all():
            user = await self.user_repo.get_by_id(view.viewer_id)
            viewers.append(
                StoryViewerResponse(
                    user_id=view.viewer_id,
                    name=user.full_name if user else None,
                    avatar_url=user.avatar_url if user else None,
                    viewed_at=view.viewed_at,
                )
            )
        return viewers

    async def delete_story(self, story_id: UUID, user_id: UUID) -> None:
        story = await self.session.get(Story, story_id)
        if story is None or story.user_id != user_id:
            raise NotFoundError("Story not found")
        await self.session.delete(story)
        await self.session.commit()

    async def expire_stories(self) -> int:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(delete(Story).where(Story.expires_at < now))
        await self.session.commit()
        return result.rowcount or 0