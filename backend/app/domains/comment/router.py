"""Comment domain API routes."""

from uuid import UUID

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUserDep, DbSessionDep, OptionalCurrentUserDep, RedisDep, RedisDep
from app.domains.comment.schemas import CommentCreate, CommentResponse
from app.domains.comment.service import CommentService
from app.domains.like.schemas import LikeToggleResponse
from app.domains.like.service import LikeService

router = APIRouter(tags=["Comments"])


@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
async def list_post_comments(
    post_id: UUID,
    db: DbSessionDep,
    limit: int = Query(default=20, ge=1, le=100),
    after_id: UUID | None = None,
    current_user: OptionalCurrentUserDep = None,
) -> list[CommentResponse]:
    viewer_id = current_user.id if current_user else None
    return await CommentService(db).list_post_comments(
        post_id, limit=limit, after_id=after_id, viewer_id=viewer_id
    )


@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=201)
async def create_comment(
    post_id: UUID,
    body: CommentCreate,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> CommentResponse:
    return await CommentService(db).add_comment(
        post_id, current_user.id, body, redis=redis
    )


@router.get("/comments/{comment_id}/replies", response_model=list[CommentResponse])
async def list_comment_replies(
    comment_id: UUID,
    db: DbSessionDep,
    limit: int = Query(default=10, ge=1, le=50),
    page: int = Query(default=1, ge=1),
    current_user: OptionalCurrentUserDep = None,
) -> list[CommentResponse]:
    viewer_id = current_user.id if current_user else None
    return await CommentService(db).list_replies(
        comment_id, limit=limit, page=page, viewer_id=viewer_id
    )


@router.delete("/comments/{comment_id}", response_model=CommentResponse)
async def delete_comment(
    comment_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> CommentResponse:
    return await CommentService(db).soft_delete(comment_id, current_user.id)


@router.post("/comments/{comment_id}/like", response_model=LikeToggleResponse)
async def toggle_comment_like(
    comment_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> LikeToggleResponse:
    return await LikeService(db).toggle_comment_like(current_user.id, comment_id)