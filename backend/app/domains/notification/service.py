"""Notification domain business logic."""

from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.common.exceptions import NotFoundError
from app.domains.notification.models import Notification
from app.domains.notification.repository import NotificationRepository
from app.domains.notification.schemas import NotificationResponse, UnreadCountResponse
from app.ws.events import publish_event

UNREAD_COUNT_TTL = 30


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = NotificationRepository(session)

    async def create_notification(
        self,
        user_id: UUID,
        type: str,
        title: str,
        body: str,
        data_dict: dict | None,
        *,
        redis: aioredis.Redis | None = None,
    ) -> NotificationResponse:
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            body=body,
            data=data_dict,
        )
        created = await self.repo.create(notification)
        await self.session.commit()
        await self.session.refresh(created)
        response = NotificationResponse.model_validate(created)
        if redis is not None:
            await redis.delete(f"notifications:unread:{user_id}")
            await publish_event(
                redis,
                f"user:{user_id}",
                "notification",
                response.model_dump(mode="json"),
            )
        try:
            from app.tasks.push import send_fcm_push

            send_fcm_push.delay(str(user_id), title, body, data_dict or {})
        except Exception:
            pass
        return response

    async def list_notifications(
        self,
        user_id: UUID,
        *,
        is_read: bool | None = None,
        limit: int = 30,
    ) -> list[NotificationResponse]:
        rows = await self.repo.list_for_user(user_id, is_read=is_read, limit=limit)
        return [NotificationResponse.model_validate(n) for n in rows]

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> NotificationResponse:
        row = await self.repo.mark_read(notification_id, user_id)
        if row is None:
            raise NotFoundError("Notification not found")
        await self.session.commit()
        return NotificationResponse.model_validate(row)

    async def mark_all_read(self, user_id: UUID) -> dict[str, int]:
        count = await self.repo.mark_all_read(user_id)
        await self.session.commit()
        return {"updated": count}

    async def unread_count(
        self,
        user_id: UUID,
        redis: aioredis.Redis | None = None,
    ) -> UnreadCountResponse:
        cache_key = f"notifications:unread:{user_id}"
        if redis is not None:
            cached = await redis.get(cache_key)
            if cached is not None:
                return UnreadCountResponse(count=int(cached))
        count = await self.repo.unread_count(user_id)
        if redis is not None:
            await redis.set(cache_key, str(count), ex=UNREAD_COUNT_TTL)
        return UnreadCountResponse(count=count)