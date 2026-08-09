"""Redis cache for discovery list — orjson payload as UTF-8 string (decode_responses Redis)."""

from __future__ import annotations

import asyncio
import hashlib

import redis.asyncio as aioredis

from app.domains.discovery.geohash import encode as geohash_encode

PLACEHOLDER = "__LOCK__"


def cache_key(
    *,
    lat: float,
    lng: float,
    radius_m: int,
    sort: str,
    filters_hash: str,
    cursor: str,
) -> str:
    gh = geohash_encode(lat, lng, 6)
    return f"disc:v1:{gh}:{radius_m}:{sort}:{filters_hash}:{cursor or '-'}"


def filters_hash(
    *,
    q: str | None,
    min_rating: float | None,
    available_now: bool | None,
    amenities_mask: int,
) -> str:
    raw = f"{q or ''}|{min_rating or ''}|{available_now}|{amenities_mask}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


def etag_for(payload: bytes) -> str:
    return hashlib.md5(payload).hexdigest()


class DiscoveryCache:
    def __init__(self, redis: aioredis.Redis) -> None:
        self.redis = redis

    async def get(self, key: str) -> bytes | None:
        raw = await self.redis.get(key)
        if raw is None or raw == PLACEHOLDER:
            return None
        if isinstance(raw, bytes):
            return raw
        return raw.encode()

    async def set(self, key: str, payload: bytes, *, available_now_filter: bool) -> None:
        ttl = 30 if available_now_filter else 60
        await self.redis.set(key, payload.decode(), ex=ttl)

    async def acquire_lock(self, key: str) -> bool:
        ok = await self.redis.set(key, PLACEHOLDER, nx=True, ex=5)
        return bool(ok)

    async def wait_and_get(self, key: str, *, attempts: int = 4) -> bytes | None:
        for _ in range(attempts):
            await asyncio.sleep(0.05)
            hit = await self.get(key)
            if hit is not None:
                return hit
        return None
