"""Online status business logic."""

from datetime import datetime, timezone
from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.friend.models import Friendship
from app.domains.online.models import UserLastSeen
from app.domains.online.schemas import OnlineStatusResponse, StatusPrivacyUpdate
from app.ws.events import publish_to_user

ONLINE_TTL = 60
ONLINE_KEY = "online:{}"
LAST_SEEN_KEY = "last_seen:{}"


class OnlineStatusService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def set_user_online(self, user_id: UUID, redis: aioredis.Redis) -> None:
        uid = str(user_id)
        await redis.setex(ONLINE_KEY.format(uid), ONLINE_TTL, "1")
        now = datetime.now(timezone.utc)
        await redis.set(LAST_SEEN_KEY.format(uid), now.isoformat())
        await self._upsert_last_seen(user_id, now)
        await self.session.commit()
        await self._broadcast_status(user_id, True, redis)

    async def set_user_offline(self, user_id: UUID, redis: aioredis.Redis) -> None:
        uid = str(user_id)
        await redis.delete(ONLINE_KEY.format(uid))
        now = datetime.now(timezone.utc)
        await redis.set(LAST_SEEN_KEY.format(uid), now.isoformat())
        await self._upsert_last_seen(user_id, now)
        await self.session.commit()
        await self._broadcast_status(user_id, False, redis)

    async def heartbeat(self, user_id: UUID, redis: aioredis.Redis) -> None:
        await self.set_user_online(user_id, redis)

    async def is_user_online(self, user_id: UUID, redis: aioredis.Redis | None) -> bool:
        if redis is None:
            return False
        return bool(await redis.exists(ONLINE_KEY.format(str(user_id))))

    async def get_status(
        self, user_id: UUID, redis: aioredis.Redis | None
    ) -> OnlineStatusResponse:
        is_online = await self.is_user_online(user_id, redis)
        last_seen = await self._get_last_seen(user_id, redis)
        return OnlineStatusResponse(
            user_id=user_id,
            is_online=is_online,
            last_seen_at=last_seen,
            last_seen_display=self._format_last_seen(last_seen, is_online),
        )

    async def update_privacy(self, user_id: UUID, data: StatusPrivacyUpdate) -> None:
        await self._upsert_last_seen(user_id, datetime.now(timezone.utc), data.show_to)
        await self.session.commit()

    async def _upsert_last_seen(
        self, user_id: UUID, at: datetime, privacy: str | None = None
    ) -> None:
        result = await self.session.execute(
            select(UserLastSeen).where(UserLastSeen.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        if row:
            row.last_seen_at = at
            if privacy:
                row.status_privacy = privacy
        else:
            self.session.add(
                UserLastSeen(
                    user_id=user_id,
                    last_seen_at=at,
                    status_privacy=privacy or "friends",
                )
            )

    async def _get_last_seen(
        self, user_id: UUID, redis: aioredis.Redis | None
    ) -> datetime | None:
        if redis:
            raw = await redis.get(LAST_SEEN_KEY.format(str(user_id)))
            if raw:
                return datetime.fromisoformat(raw)
        result = await self.session.execute(
            select(UserLastSeen).where(UserLastSeen.user_id == user_id)
        )
        row = result.scalar_one_or_none()
        return row.last_seen_at if row else None

    def _format_last_seen(self, last_seen: datetime | None, is_online: bool) -> str:
        if is_online:
            return "Active now"
        if last_seen is None:
            return "Long time ago"
        diff = datetime.now(timezone.utc) - last_seen
        if diff.total_seconds() < 60:
            return "Just now"
        if diff.total_seconds() < 3600:
            return f"Active {int(diff.total_seconds() / 60)}m ago"
        if diff.total_seconds() < 86400:
            return f"Active {int(diff.total_seconds() / 3600)}h ago"
        if diff.days == 1:
            return "Active yesterday"
        return f"Active {diff.days}d ago"

    async def _broadcast_status(
        self, user_id: UUID, is_online: bool, redis: aioredis.Redis
    ) -> None:
        result = await self.session.execute(
            select(Friendship).where(
                or_(Friendship.user1_id == user_id, Friendship.user2_id == user_id)
            )
        )
        event_type = "user_online" if is_online else "user_offline"
        now = datetime.now(timezone.utc).isoformat()
        for f in result.scalars().all():
            friend_id = f.user2_id if f.user1_id == user_id else f.user1_id
            await publish_to_user(
                redis,
                friend_id,
                {"type": event_type, "user_id": str(user_id), "last_seen": now},
            )