"""Discovery API — single list endpoint, orjson bytes, Redis cache, ETag."""

from __future__ import annotations

from typing import Annotated, Literal

import orjson
from fastapi import APIRouter, Depends, Header, Query, Request, Response
from fastapi.responses import Response as RawResponse
from pydantic import BaseModel, Field

from app.core.dependencies import RedisDep
from app.domains.discovery.cache import DiscoveryCache, cache_key, etag_for, filters_hash
from app.domains.discovery.db import get_discovery_pool
from app.domains.discovery.service import fetch_centres

router = APIRouter(prefix="/discovery", tags=["Discovery"])


class DiscoveryQuery(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    radius_m: int = Field(default=5000, ge=200, le=50000)
    sort: Literal["distance", "rating", "relevance"] = "distance"
    q: str | None = Field(default=None, max_length=100)
    min_rating: float | None = Field(default=None, ge=0, le=5)
    available_now: bool | None = None
    amenities_mask: int = Field(default=0, ge=0)
    cursor: str | None = None
    limit: int = Field(default=20, ge=1, le=40)


def _parse_query(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_m: int = Query(default=5000, ge=200, le=50000),
    sort: Literal["distance", "rating", "relevance"] = Query(default="distance"),
    q: str | None = Query(default=None, max_length=100),
    min_rating: float | None = Query(default=None, ge=0, le=5),
    available_now: bool | None = Query(default=None),
    amenities_mask: int = Query(default=0, ge=0),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=40),
) -> DiscoveryQuery:
    return DiscoveryQuery(
        lat=lat,
        lng=lng,
        radius_m=radius_m,
        sort=sort,
        q=q,
        min_rating=min_rating,
        available_now=available_now,
        amenities_mask=amenities_mask,
        cursor=cursor,
        limit=limit,
    )


@router.get("/centres")
async def list_centres(
    request: Request,
    redis: RedisDep,
    params: Annotated[DiscoveryQuery, Depends(_parse_query)],
    if_none_match: Annotated[str | None, Header()] = None,
) -> Response:
    """Nearby gaming centres — one SQL, Redis geohash cache, ETag/304."""
    fhash = filters_hash(
        q=params.q,
        min_rating=params.min_rating,
        available_now=params.available_now,
        amenities_mask=params.amenities_mask,
    )
    key = cache_key(
        lat=params.lat,
        lng=params.lng,
        radius_m=params.radius_m,
        sort=params.sort,
        filters_hash=fhash,
        cursor=params.cursor or "",
    )
    cache = DiscoveryCache(redis)

    cached = await cache.get(key)
    if cached is not None:
        tag = etag_for(cached)
        if if_none_match and if_none_match.strip('"') == tag:
            return RawResponse(status_code=304, headers={"ETag": f'"{tag}"'})
        return RawResponse(
            content=cached,
            media_type="application/json",
            headers={
                "ETag": f'"{tag}"',
                "Cache-Control": "private, max-age=30",
                "X-Cache": "HIT",
            },
        )

    # Stampede guard
    got_lock = await cache.acquire_lock(key)
    if not got_lock:
        waited = await cache.wait_and_get(key)
        if waited is not None:
            tag = etag_for(waited)
            return RawResponse(
                content=waited,
                media_type="application/json",
                headers={
                    "ETag": f'"{tag}"',
                    "Cache-Control": "private, max-age=30",
                    "X-Cache": "WAIT",
                },
            )

    pool = await get_discovery_pool()
    async with pool.acquire() as conn:
        items, next_cursor = await fetch_centres(
            conn,
            lat=params.lat,
            lng=params.lng,
            radius_m=params.radius_m,
            limit=params.limit,
            cursor=params.cursor,
            q=params.q,
            min_rating=params.min_rating,
            available_now=params.available_now,
            amenities_mask=params.amenities_mask,
            sort=params.sort,
        )

    body = {
        "items": items,
        "next_cursor": next_cursor,
        "radius_m": params.radius_m,
        "sort": params.sort,
        "count": len(items),
    }
    payload = orjson.dumps(body)
    await cache.set(
        key,
        payload,
        available_now_filter=bool(params.available_now),
    )
    tag = etag_for(payload)
    if if_none_match and if_none_match.strip('"') == tag:
        return RawResponse(status_code=304, headers={"ETag": f'"{tag}"'})
    return RawResponse(
        content=payload,
        media_type="application/json",
        headers={
            "ETag": f'"{tag}"',
            "Cache-Control": "private, max-age=30",
            "X-Cache": "MISS",
        },
    )
