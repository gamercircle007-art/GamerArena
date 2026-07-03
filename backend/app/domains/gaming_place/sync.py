"""Sync gaming places from the external projectX PostgreSQL catalog."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.gaming_place.models import GamingPlace

logger = logging.getLogger(__name__)


def _normalize_source_url(url: str) -> str:
    return (
        url.replace("postgresql+asyncpg://", "postgresql://")
        .replace("postgresql+psycopg://", "postgresql://")
    )


def _parse_json(value):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return value


async def sync_gaming_places(session: AsyncSession, source_url: str) -> int:
    """Upsert all rows from the source ``gaming_places`` table into the app DB."""
    import asyncpg

    conn = await asyncpg.connect(_normalize_source_url(source_url))
    try:
        rows = await conn.fetch("SELECT * FROM gaming_places ORDER BY name")
    finally:
        await conn.close()

    if not rows:
        logger.warning("gaming_places_sync_empty")
        return 0

    synced = 0
    for row in rows:
        payload = {
            "id": UUID(str(row["id"])),
            "google_place_id": row["google_place_id"],
            "name": row["name"],
            "address": row["address"],
            "city_id": UUID(str(row["city_id"])),
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "rating": row["rating"],
            "user_ratings_total": row["user_ratings_total"],
            "phone": row["phone"],
            "website": row["website"],
            "google_maps_url": row["google_maps_url"],
            "business_status": row["business_status"],
            "primary_type": row["primary_type"],
            "types": _parse_json(row["types"]),
            "opening_hours": _parse_json(row["opening_hours"]),
            "image_url": row["image_url"],
            "photo_name": row["photo_name"],
            "photos": _parse_json(row["photos"]),
            "raw_data": _parse_json(row["raw_data"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        update_cols = {
            key: payload[key]
            for key in payload
            if key not in ("id", "google_place_id")
        }
        stmt = sqlite_insert(GamingPlace).values(**payload)
        stmt = stmt.on_conflict_do_update(
            index_elements=[GamingPlace.google_place_id],
            set_=update_cols,
        )
        await session.execute(stmt)
        synced += 1

    await session.commit()
    logger.info("gaming_places_synced", extra={"count": synced})
    return synced


async def gaming_place_count(session: AsyncSession) -> int:
    result = await session.execute(select(GamingPlace.id).limit(1))
    return 1 if result.scalar_one_or_none() else 0