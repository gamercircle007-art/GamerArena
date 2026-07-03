"""Feed domain API routes."""

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUserDep, DbSessionDep, RedisDep
from app.domains.feed.schemas import FeedResponse
from app.domains.feed.service import FeedService

router = APIRouter(prefix="/feed", tags=["Feed"])


@router.get("", response_model=FeedResponse)
async def get_feed(
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
    lat: float | None = None,
    lng: float | None = None,
) -> FeedResponse:
    return await FeedService(db).build_feed(
        current_user.id,
        page,
        limit,
        redis,
        user_lat=lat,
        user_lng=lng,
    )