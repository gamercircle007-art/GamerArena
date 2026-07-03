"""Like domain API routes."""

from uuid import UUID

from fastapi import APIRouter

from app.core.dependencies import CurrentUserDep, DbSessionDep
from app.domains.like.schemas import LikeCreate, LikeToggleResponse
from app.domains.like.service import LikeService

router = APIRouter(prefix="/likes", tags=["Likes"])


@router.post("", response_model=LikeToggleResponse)
async def create_like(
    body: LikeCreate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> LikeToggleResponse:
    return await LikeService(db).add_like(current_user.id, body.target_type, body.target_id)


@router.delete("/{target_type}/{target_id}", response_model=LikeToggleResponse)
async def delete_like(
    target_type: str,
    target_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> LikeToggleResponse:
    return await LikeService(db).remove_like(current_user.id, target_type, target_id)