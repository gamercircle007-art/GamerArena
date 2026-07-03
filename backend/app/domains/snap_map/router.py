"""Snap map and profile API routes."""

from uuid import UUID

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUserDep, DbSessionDep, OptionalCurrentUserDep, RedisDep
from app.domains.friend.schemas import UserSummary
from app.domains.snap_map.schemas import (
    GhostModeUpdate,
    LocationPrivacyUpdate,
    LocationUpdate,
    ProfileUpdate,
    PublicProfileResponse,
    SnapMapUser,
)
from app.domains.snap_map.service import SnapMapService

router = APIRouter(tags=["Snap Map", "Profile"])


@router.put("/location/update", status_code=204)
async def update_location(
    body: LocationUpdate,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> None:
    await SnapMapService(db).update_location(current_user.id, body, redis)


@router.get("/location/ghost-mode")
async def get_ghost_mode(
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict:
    return await SnapMapService(db).get_ghost_mode(current_user.id)


@router.put("/location/ghost-mode")
async def set_ghost_mode(
    body: GhostModeUpdate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict:
    return await SnapMapService(db).set_ghost_mode(current_user.id, body)


@router.get("/location/friends-map", response_model=list[SnapMapUser])
async def friends_map(
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> list[SnapMapUser]:
    return await SnapMapService(db).get_friends_on_map(current_user.id, redis)


@router.put("/location/privacy", status_code=204)
async def set_location_privacy(
    body: LocationPrivacyUpdate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> None:
    await SnapMapService(db).set_location_privacy(current_user.id, body)


@router.get("/users/{user_id}/profile", response_model=PublicProfileResponse)
async def get_user_profile(
    user_id: UUID,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: OptionalCurrentUserDep = None,
) -> PublicProfileResponse:
    viewer_id = current_user.id if current_user else None
    return await SnapMapService(db).get_public_profile(user_id, viewer_id, redis)


@router.put("/users/me/profile")
async def update_my_profile(
    body: ProfileUpdate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict:
    profile = await SnapMapService(db).update_profile(current_user.id, body)
    return {"user_id": str(profile.user_id), "updated": True}


@router.get("/users/search", response_model=list[UserSummary])
async def search_users(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    q: str = Query(min_length=1),
) -> list[UserSummary]:
    users = await SnapMapService(db).search_users(q)
    return [UserSummary.model_validate(u) for u in users]


@router.get("/users/me/qr-code")
async def get_qr_code(current_user: CurrentUserDep) -> dict:
    return {
        "qr_data": f"gamer-circle://profile/{current_user.id}",
        "username": current_user.username,
    }