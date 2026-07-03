"""In-app + push notifications for social events."""

from uuid import UUID

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.notification.service import NotificationService
from app.domains.online.service import OnlineStatusService


async def notify_user(
    session: AsyncSession,
    redis: aioredis.Redis,
    user_id: UUID,
    *,
    type: str,
    title: str,
    body: str,
    data: dict | None = None,
    skip_if_online: bool = False,
) -> None:
    """Create in-app notification and queue FCM push (stub when offline)."""
    if skip_if_online and await OnlineStatusService(session).is_user_online(user_id, redis):
        return
    await NotificationService(session).create_notification(
        user_id,
        type,
        title,
        body,
        data,
        redis=redis,
    )