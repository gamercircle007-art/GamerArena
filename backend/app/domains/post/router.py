"""Post domain API routes."""

from uuid import UUID

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUserDep, DbSessionDep, OptionalCurrentUserDep, RedisDep
from app.domains.post.schemas import PostCreate, PostResponse
from app.domains.post.service import PostService

router = APIRouter(prefix="/posts", tags=["Posts"])


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    body: PostCreate,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> PostResponse:
    service = PostService(db)
    return await service.create_post(
        current_user.id,
        body,
        redis,
        user_role=current_user.role.value,
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    db: DbSessionDep,
    current_user: OptionalCurrentUserDep = None,
) -> PostResponse:
    viewer_id = current_user.id if current_user else None
    return await PostService(db).get_post(post_id, viewer_id)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> None:
    await PostService(db).delete_post(post_id, current_user.id)