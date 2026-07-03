"""Geo domain API routes."""

from datetime import datetime

from fastapi import APIRouter, Query

from app.core.dependencies import DbSessionDep, RedisDep
from app.domains.geo.schemas import (
    NearbyParlorResponse,
    NearbyTournamentResponse,
    ParlorSearchResponse,
)
from app.domains.geo.service import GeoService

router = APIRouter(prefix="/geo", tags=["Geo"])


@router.get("/nearby-parlors", response_model=list[NearbyParlorResponse])
async def nearby_parlors(
    db: DbSessionDep,
    redis: RedisDep,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: float = Query(default=5000, ge=100, le=50000),
    game_type: str | None = None,
    limit: int = Query(default=20, ge=1, le=50),
) -> list[NearbyParlorResponse]:
    return await GeoService(db).nearby_parlors(
        lat, lng, radius, game_type=game_type, limit=limit, redis=redis
    )


@router.get("/search-parlors", response_model=ParlorSearchResponse)
async def search_parlors(
    db: DbSessionDep,
    redis: RedisDep,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: float = Query(default=5000, ge=100, le=50000),
    q: str | None = None,
    min_rating: float | None = Query(default=None, ge=0, le=5),
    open_now: bool | None = None,
    city: str | None = None,
    state: str | None = None,
    game_type: str | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=50),
) -> ParlorSearchResponse:
    return await GeoService(db).search_parlors(
        lat,
        lng,
        radius_m=radius,
        q=q,
        min_rating=min_rating,
        open_now=open_now,
        city=city,
        state=state,
        game_type=game_type,
        page=page,
        limit=limit,
        redis=redis,
    )


@router.get("/nearby-tournaments", response_model=list[NearbyTournamentResponse])
async def nearby_tournaments(
    db: DbSessionDep,
    redis: RedisDep,
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: float = Query(default=5000, ge=100, le=50000),
    status: str | None = Query(default="open"),
    date_from: datetime | None = None,
    limit: int = Query(default=20, ge=1, le=50),
) -> list[NearbyTournamentResponse]:
    return await GeoService(db).nearby_tournaments(
        lat,
        lng,
        radius,
        status=status,
        date_from=date_from,
        limit=limit,
        redis=redis,
    )