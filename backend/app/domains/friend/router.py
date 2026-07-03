"""Friend system API routes."""

from uuid import UUID

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUserDep, DbSessionDep, RedisDep
from app.domains.friend.schemas import (
    FriendRequestCreate,
    FriendRequestResponse,
    FriendSuggestion,
    FriendshipResponse,
)
from app.domains.friend.service import FriendService

router = APIRouter(prefix="/friends", tags=["Friends"])


@router.post("/request")
async def send_friend_request(
    body: FriendRequestCreate,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> dict:
    return await FriendService(db).send_friend_request(current_user.id, body.user_id, redis)


@router.get("/requests", response_model=list[FriendRequestResponse])
async def list_incoming_requests(
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> list[FriendRequestResponse]:
    return await FriendService(db).list_incoming_requests(current_user.id)


@router.get("/requests/sent", response_model=list[FriendRequestResponse])
async def list_sent_requests(
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> list[FriendRequestResponse]:
    return await FriendService(db).list_sent_requests(current_user.id)


@router.post("/requests/{request_id}/accept")
async def accept_request(
    request_id: UUID,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> dict:
    return await FriendService(db).accept_friend_request(request_id, current_user.id, redis)


@router.post("/requests/{request_id}/decline")
async def decline_request(
    request_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict:
    return await FriendService(db).decline_friend_request(request_id, current_user.id)


@router.delete("/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_request(
    request_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> None:
    await FriendService(db).cancel_friend_request(request_id, current_user.id)


@router.get("", response_model=list[FriendshipResponse])
async def list_friends(
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> list[FriendshipResponse]:
    return await FriendService(db).list_friends(current_user.id)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfriend(
    user_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> None:
    await FriendService(db).unfriend(current_user.id, user_id)


@router.get("/suggestions", response_model=list[FriendSuggestion])
async def friend_suggestions(
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> list[FriendSuggestion]:
    return await FriendService(db).get_suggestions(current_user.id)


