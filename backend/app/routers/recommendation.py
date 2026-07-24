"""Recommendation / algorithm routers.

Endpoints:
- GET /feed/ranked , /feed/reels , /feed/trending , /feed/discover
- POST /interactions/track  (also exposed under /feed for compat)
- GET /users/me/interests
- GET /search/smart
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text

from app.core.dependencies import CurrentUserDep, DbSessionDep, OptionalCurrentUserDep, RedisDep
from app.models.recommendation import TrendingItem, UserInteraction, UserInterestProfile
from app.schemas.recommendation import (
    FeedResponse,
    TrackInteractionRequest,
    UserInterestResponse,
)
from app.services.recommendation_engine import (
    build_personalized_feed,
    compute_trending,
    compute_user_interests,
    smart_search,
    track_interaction,
    track_search,
)

# Primary recommendation router (mounted at /api/v1 )
router = APIRouter(tags=["Feed & Recommendation"])


# --- Feed endpoints under /feed (included with /api/v1 prefix => /api/v1/feed/...) ---
feed_router = APIRouter(prefix="/feed")


@feed_router.get("/ranked", response_model=FeedResponse)
async def get_ranked_feed(
    db: DbSessionDep,
    redis: RedisDep,
    current_user: OptionalCurrentUserDep = None,
    feed_type: str = Query("home"),
    page: int = 1,
    limit: int = 20,
    lat: float | None = None,
    lng: float | None = None,
):
    user_id = current_user.id if current_user else None
    if user_id is None:
        return {"items": [], "page": page, "feed_type": feed_type, "personalized": False}
    data = await build_personalized_feed(db, redis, user_id, feed_type, page, limit, lat, lng)
    # ensure shape
    return data


@feed_router.get("/reels")
async def get_reels_feed(
    db: DbSessionDep,
    redis: RedisDep,
    current_user: OptionalCurrentUserDep = None,
    page: int = 1,
    limit: int = 20,
):
    # Reels-focused: delegate to ranked with filter in future; for now use home + reel bias
    user_id = current_user.id if current_user else None
    if not user_id:
        return {"items": [], "page": page, "feed_type": "reels", "personalized": False}
    data = await build_personalized_feed(db, redis, user_id, "reels", page, limit)
    return data


@feed_router.get("/trending")
async def get_trending_feed(
    db: DbSessionDep,
    window: str = Query("6h"),
    game_type: str | None = None,
    city: str | None = None,
    limit: int = 20,
):
    # For simplicity read from table; in prod use redis sorted set too
    from sqlalchemy import select
    from app.models.recommendation import TrendingItem
    wh = window
    q = select(TrendingItem).where(TrendingItem.window == wh).order_by(TrendingItem.trending_score.desc()).limit(limit)
    rows = await db.execute(q)
    items = [
        {
            "content_id": str(t.content_id),
            "content_type": t.content_type,
            "trending_score": t.trending_score,
            "window": t.window,
        }
        for t in rows.scalars()
    ]
    return {"items": items, "window": wh, "computed_at": datetime.utcnow()}


@feed_router.get("/discover")
async def get_discover_feed(
    db: DbSessionDep,
    redis: RedisDep,
    current_user: OptionalCurrentUserDep = None,
    page: int = 1,
    limit: int = 20,
):
    user_id = current_user.id if current_user else None
    if not user_id:
        return {"items": [], "page": page, "feed_type": "discover", "personalized": False}
    # 50/50 mix stub: call ranked
    return await build_personalized_feed(db, redis, user_id, "discover", page, limit)


# Mount feed sub
router.include_router(feed_router)


# --- Interactions (POST /api/v1/interactions/track ) ---
interactions_router = APIRouter(prefix="/interactions")


@interactions_router.post("/track", status_code=202)
async def track_interaction_endpoint(
    body: TrackInteractionRequest,
    db: DbSessionDep,
    redis: RedisDep,
    current_user: CurrentUserDep,
):
    await track_interaction(
        db,
        redis,
        current_user.id,
        body.content_type,
        body.content_id,
        body.action,
        body.view_duration_ms,
        body.scroll_depth_pct,
        body.session_id,
        body.source,
        body.position_in_feed,
        body.user_lat,
        body.user_lng,
        body.device_type,
    )
    return {"accepted": True}


router.include_router(interactions_router)


# --- User interests ---
@router.get("/users/me/interests", response_model=UserInterestResponse)
async def get_my_interests(
    db: DbSessionDep,
    current_user: CurrentUserDep,
):
    profile = await compute_user_interests(db, current_user.id)
    return profile


# Smart search available via engine; existing /search in domains/search/router.py remains primary.
# To use algo: can call smart_search directly or extend.


# --- Admin algo (basic) ---
admin_algo = APIRouter(prefix="/admin/algo")


@admin_algo.get("/stats")
async def algo_stats(db: DbSessionDep):
    from sqlalchemy import func, select
    total = (await db.execute(select(func.count()).select_from(UserInteraction))).scalar() or 0
    prof = (await db.execute(select(func.count()).select_from(UserInterestProfile))).scalar() or 0
    tr = (await db.execute(select(func.count()).select_from(TrendingItem))).scalar() or 0
    return {"total_interactions": total, "profiles_computed": prof, "trending_count": tr}


@admin_algo.post("/refresh-trending")
async def force_trending(db: DbSessionDep):
    n = await compute_trending(db, 6)
    return {"refreshed": n}


