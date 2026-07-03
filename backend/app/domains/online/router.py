"""Online status API routes."""

from uuid import UUID

from fastapi import APIRouter

from app.core.dependencies import CurrentUserDep, DbSessionDep, RedisDep
from app.domains.online.schemas import OnlineStatusResponse, StatusPrivacyUpdate
from app.domains.online.service import OnlineStatusService

router = APIRouter(tags=["Online Status"])


@router.get("/users/{user_id}/status", response_model=OnlineStatusResponse)
async def get_user_status(
    user_id: UUID,
    db: DbSessionDep,
    redis: RedisDep,
) -> OnlineStatusResponse:
    return await OnlineStatusService(db).get_status(user_id, redis)


@router.put("/users/me/status-privacy", status_code=204)
async def update_status_privacy(
    body: StatusPrivacyUpdate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> None:
    await OnlineStatusService(db).update_privacy(current_user.id, body)


@router.post("/users/me/heartbeat", status_code=204)
async def heartbeat(
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> None:
    await OnlineStatusService(db).heartbeat(current_user.id, redis)