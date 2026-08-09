"""Reel domain API routes."""

from uuid import UUID

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUserDep, DbSessionDep, OptionalCurrentUserDep, RedisDep
from app.domains.like.schemas import LikeToggleResponse
from app.domains.like.service import LikeService
from app.domains.reel.schemas import (
    DemoMusicTrack,
    ReelBookmarkResponse,
    ReelCommentCreate,
    ReelCommentResponse,
    ReelCreate,
    ReelFeedResponse,
    ReelReportCreate,
    ReelResponse,
    ReelShareResponse,
    ReelUpdate,
    ReelViewResponse,
    UserFollowResponse,
)
from app.domains.reel.service import ReelService

router = APIRouter(prefix="/reels", tags=["Reels"])


@router.get("/feed", response_model=ReelFeedResponse)
async def reel_feed(
    db: DbSessionDep,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=30),
    sort: str = Query(default="trending"),
    current_user: OptionalCurrentUserDep = None,
) -> ReelFeedResponse:
    """Public reel feed. Empty page if reels schema/data is broken in prod."""
    viewer_id = current_user.id if current_user else None
    try:
        return await ReelService(db).feed(
            viewer_id=viewer_id, page=page, limit=limit, sort=sort
        )
    except Exception:  # noqa: BLE001 — never 500 the Reels tab in prod
        return ReelFeedResponse(items=[], page=page, limit=limit, has_more=False)



@router.get("/search", response_model=ReelFeedResponse)
async def search_reels(
    db: DbSessionDep,
    q: str = Query(..., min_length=1),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=30),
    sort: str = Query(default="trending"),
    current_user: OptionalCurrentUserDep = None,
) -> ReelFeedResponse:
    viewer_id = current_user.id if current_user else None
    return await ReelService(db).search_reels(
        q, viewer_id=viewer_id, page=page, limit=limit, sort=sort
    )


@router.get("/music/demo", response_model=list[DemoMusicTrack])
async def demo_music(db: DbSessionDep) -> list[DemoMusicTrack]:
    return await ReelService(db).demo_music()


@router.post("", response_model=ReelResponse, status_code=201)
async def create_reel(
    body: ReelCreate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> ReelResponse:
    return await ReelService(db).create_reel(current_user.id, body)


@router.get("/{reel_id}", response_model=ReelResponse)
async def get_reel(
    reel_id: UUID,
    db: DbSessionDep,
    current_user: OptionalCurrentUserDep = None,
) -> ReelResponse:
    viewer_id = current_user.id if current_user else None
    return await ReelService(db).get_reel(reel_id, viewer_id)


@router.patch("/{reel_id}", response_model=ReelResponse)
async def update_reel(
    reel_id: UUID,
    body: ReelUpdate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> ReelResponse:
    return await ReelService(db).update_reel(current_user.id, reel_id, body)


@router.delete("/{reel_id}", status_code=204)
async def delete_reel(
    reel_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> None:
    await ReelService(db).delete_reel(current_user.id, reel_id)


@router.post("/{reel_id}/view", response_model=ReelViewResponse)
async def record_view(
    reel_id: UUID,
    db: DbSessionDep,
    current_user: OptionalCurrentUserDep = None,
) -> ReelViewResponse:
    viewer_id = current_user.id if current_user else None
    return await ReelService(db).record_view(reel_id, viewer_id)


@router.post("/{reel_id}/bookmark", response_model=ReelBookmarkResponse)
async def toggle_bookmark(
    reel_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> ReelBookmarkResponse:
    return await ReelService(db).toggle_bookmark(current_user.id, reel_id)


@router.post("/{reel_id}/share", response_model=ReelShareResponse)
async def record_share(reel_id: UUID, db: DbSessionDep) -> ReelShareResponse:
    return await ReelService(db).record_share(reel_id)


@router.post("/{reel_id}/report", status_code=204)
async def report_reel(
    reel_id: UUID,
    body: ReelReportCreate,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> None:
    await ReelService(db).report_reel(reel_id, current_user.id, body.reason)


@router.post("/{reel_id}/like", response_model=LikeToggleResponse)
async def like_reel(
    reel_id: UUID,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> LikeToggleResponse:
    result = await LikeService(db).add_like(current_user.id, "reel", reel_id)
    await ReelService(db).notify_like(reel_id, current_user.id, redis=redis)
    return result


@router.delete("/{reel_id}/like", response_model=LikeToggleResponse)
async def unlike_reel(
    reel_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> LikeToggleResponse:
    return await LikeService(db).remove_like(current_user.id, "reel", reel_id)


@router.get("/{reel_id}/comments", response_model=list[ReelCommentResponse])
async def list_reel_comments(
    reel_id: UUID,
    db: DbSessionDep,
    limit: int = Query(default=20, ge=1, le=100),
    after_id: UUID | None = None,
    current_user: OptionalCurrentUserDep = None,
) -> list[ReelCommentResponse]:
    viewer_id = current_user.id if current_user else None
    return await ReelService(db).list_comments(
        reel_id, viewer_id=viewer_id, limit=limit, after_id=after_id
    )


@router.post("/{reel_id}/comments", response_model=ReelCommentResponse, status_code=201)
async def create_reel_comment(
    reel_id: UUID,
    body: ReelCommentCreate,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> ReelCommentResponse:
    return await ReelService(db).add_comment(
        reel_id, current_user.id, body, redis=redis
    )


@router.get("/reel-comments/{comment_id}/replies", response_model=list[ReelCommentResponse])
async def list_reel_replies(
    comment_id: UUID,
    db: DbSessionDep,
    limit: int = Query(default=10, ge=1, le=50),
    page: int = Query(default=1, ge=1),
    current_user: OptionalCurrentUserDep = None,
) -> list[ReelCommentResponse]:
    viewer_id = current_user.id if current_user else None
    return await ReelService(db).list_replies(
        comment_id, viewer_id=viewer_id, limit=limit, page=page
    )


@router.delete("/reel-comments/{comment_id}", response_model=ReelCommentResponse)
async def delete_reel_comment(
    comment_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> ReelCommentResponse:
    return await ReelService(db).delete_comment(comment_id, current_user.id)


@router.post("/reel-comments/{comment_id}/like", response_model=LikeToggleResponse)
async def like_reel_comment(
    comment_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> LikeToggleResponse:
    return await LikeService(db).add_like(current_user.id, "reel_comment", comment_id)


@router.delete("/reel-comments/{comment_id}/like", response_model=LikeToggleResponse)
async def unlike_reel_comment(
    comment_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> LikeToggleResponse:
    return await LikeService(db).remove_like(
        current_user.id, "reel_comment", comment_id
    )


@router.post("/users/{user_id}/follow", response_model=UserFollowResponse)
async def follow_user(
    user_id: UUID,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
) -> UserFollowResponse:
    return await ReelService(db).follow_user(
        current_user.id, user_id, redis=redis
    )


@router.delete("/users/{user_id}/follow", response_model=UserFollowResponse)
async def unfollow_user(
    user_id: UUID,
    db: DbSessionDep,
    current_user: CurrentUserDep,
) -> UserFollowResponse:
    return await ReelService(db).unfollow_user(current_user.id, user_id)