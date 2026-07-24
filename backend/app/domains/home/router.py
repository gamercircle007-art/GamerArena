"""Home feed and discovery API routes."""

from fastapi import APIRouter, Query

from app.core.dependencies import DbSessionDep, OptionalCurrentUserDep, RedisDep
from app.domains.gaming_booking.schemas import CitiesResponse, HomeParlorCard, HomeResponse
from app.domains.home.service import HomeService

router = APIRouter(tags=["Home"])


@router.get("/home", response_model=HomeResponse)
async def get_home(
    db: DbSessionDep,
    redis: RedisDep,
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    city: str | None = None,
    radius: float | None = Query(default=None, ge=100, le=50000),
    pick_filter: str = Query(default="recommended"),
    current_user: OptionalCurrentUserDep = None,
) -> HomeResponse:
    if current_user and current_user.city and not city and lat is None and lng is None:
        city = current_user.city
    user_id = current_user.id if current_user else None
    return await HomeService(db).get_home(
        lat=lat,
        lng=lng,
        city=city,
        radius_m=radius,
        pick_filter=pick_filter,
        user_id=user_id,
        redis=redis,
    )


@router.get("/home/nearby", response_model=list[HomeParlorCard])
async def get_home_nearby(
    db: DbSessionDep,
    redis: RedisDep,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: float = Query(default=5000, ge=100, le=50000),
    limit: int = Query(default=20, ge=1, le=50),
) -> list[HomeParlorCard]:
    return await HomeService(db).get_nearby(lat, lng, radius_m=radius, limit=limit, redis=redis)


@router.get("/home/quick-picks", response_model=list[HomeParlorCard])
async def get_quick_picks(
    db: DbSessionDep,
    redis: RedisDep,
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    city: str | None = None,
    pick_filter: str = Query(default="recommended"),
    limit: int = Query(default=8, ge=1, le=20),
    current_user: OptionalCurrentUserDep = None,
) -> list[HomeParlorCard]:
    if current_user and current_user.city and not city and lat is None and lng is None:
        city = current_user.city
    user_id = current_user.id if current_user else None
    return await HomeService(db).get_quick_picks(
        lat=lat,
        lng=lng,
        city=city,
        pick_filter=pick_filter,
        user_id=user_id,
        limit=limit,
        redis=redis,
    )


@router.get("/cities", response_model=CitiesResponse)
async def list_cities(
    db: DbSessionDep,
    limit: int = Query(default=50, ge=1, le=100),
) -> CitiesResponse:
    return await HomeService(db).get_cities(limit=limit)