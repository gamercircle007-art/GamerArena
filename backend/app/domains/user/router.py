"""
User domain API routes.

MICROSERVICE EXTRACTION: Copy this router + service + repository + models to a new
FastAPI app. Register at /users. Auth service validates JWT and passes user_id.
"""

from uuid import UUID

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUserDep, DbSessionDep
from app.domains.booking.schemas import BookingResponse
from app.domains.booking.service import BookingService
from app.domains.follow.service import FollowService
from app.domains.parlor.schemas import ParlorSummary
from app.domains.friend.schemas import MutualFriendsResponse, UserSummary
from app.domains.friend.service import FriendService
from app.domains.user.schemas import UserLocationUpdate, UserResponse, UserUpdate
from app.domains.user.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: CurrentUserDep) -> UserResponse:
    """Return the authenticated user's profile."""
    return current_user


@router.get("/me/following", response_model=list[ParlorSummary])
async def list_my_following(
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> list[ParlorSummary]:
    return await FollowService(db).list_following(current_user.id)


@router.get("/me/bookings", response_model=list[BookingResponse])
async def list_my_bookings(
    db: DbSessionDep,
    current_user: CurrentUserDep,
    upcoming: bool | None = Query(default=None, description="Filter upcoming or past"),
) -> list[BookingResponse]:
    """List bookings for the authenticated user."""
    service = BookingService(db)
    return await service.list_user_bookings(current_user.id, upcoming=upcoming)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> UserResponse:
    """Get user by ID (authenticated). Extend with RBAC as needed."""
    _ = current_user  # Ensure authenticated; add authorization later
    service = UserService(db)
    return await service.get_user(user_id)


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    data: UserUpdate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> UserResponse:
    """Update the authenticated user's profile."""
    service = UserService(db)
    return await service.update_user(current_user.id, data)


@router.patch("/me/location", response_model=UserResponse)
async def update_current_user_location(
    data: UserLocationUpdate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> UserResponse:
    """Store the user's GPS location after they grant permission on any platform."""
    service = UserService(db)
    return await service.update_location(current_user.id, data)


@router.get("/{user_id}/mutual-friends", response_model=MutualFriendsResponse)
async def mutual_friends(
    user_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> MutualFriendsResponse:
    return await FriendService(db).get_mutual_friends(current_user.id, user_id)


@router.post("/{user_id}/block", status_code=status.HTTP_204_NO_CONTENT)
async def block_user(
    user_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> None:
    await FriendService(db).block_user(current_user.id, user_id)


@router.delete("/{user_id}/block", status_code=status.HTTP_204_NO_CONTENT)
async def unblock_user(
    user_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> None:
    await FriendService(db).unblock_user(current_user.id, user_id)


@router.get("/me/blocks", response_model=list[UserSummary])
async def list_blocks(
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> list[UserSummary]:
    return await FriendService(db).list_blocked(current_user.id)