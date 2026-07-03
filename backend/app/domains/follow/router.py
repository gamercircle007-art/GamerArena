"""Follow domain API routes."""

from uuid import UUID

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUserDep, DbSessionDep
from app.domains.follow.schemas import FollowCreate
from app.domains.follow.service import FollowService
from app.domains.parlor.schemas import ParlorSummary

router = APIRouter(prefix="/follows", tags=["Follows"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def follow_parlor(
    body: FollowCreate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> dict[str, str]:
    await FollowService(db).follow(current_user.id, body.parlor_id)
    return {"message": "Followed"}


@router.delete("/{parlor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_parlor(
    parlor_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> None:
    await FollowService(db).unfollow(current_user.id, parlor_id)