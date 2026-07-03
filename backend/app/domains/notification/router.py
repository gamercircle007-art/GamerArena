"""Notification domain API routes."""

from uuid import UUID

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUserDep, DbSessionDep, RedisDep
from app.domains.notification.schemas import NotificationResponse, UnreadCountResponse
from app.domains.notification.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    is_read: bool | None = None,
    limit: int = Query(default=30, ge=1, le=100),
) -> list[NotificationResponse]:
    return await NotificationService(db).list_notifications(
        current_user.id, is_read=is_read, limit=limit
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> UnreadCountResponse:
    return await NotificationService(db).unread_count(current_user.id, redis=redis)


@router.put("/read-all")
async def mark_all_read(
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict[str, int]:
    return await NotificationService(db).mark_all_read(current_user.id)


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> NotificationResponse:
    return await NotificationService(db).mark_read(notification_id, current_user.id)