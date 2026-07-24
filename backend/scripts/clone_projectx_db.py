#!/usr/bin/env python3
"""Clone projectX PostgreSQL catalog data into the Paythan database.

Copies all rows from projectX public tables that exist in Paythan:
  - gaming_places (required for parlors, booking, home, geo)

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/clone_projectx_db.py

Environment (optional overrides):
    GAMING_PLACES_DATABASE_URL  source, default projectx@localhost:5432/projectx
    DATABASE_URL                target, default paythan@localhost:5432/paythan
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
os.chdir(BACKEND_ROOT)

DEFAULT_SOURCE = "postgresql://projectx:projectx@localhost:5432/projectx"
DEFAULT_TARGET = "postgresql://paythan:changeme_postgres_password@localhost:5432/paythan"

GAMING_PLACES_UPSERT = """
INSERT INTO gaming_places (
    id, google_place_id, name, address, city_id,
    latitude, longitude, rating, user_ratings_total,
    phone, website, google_maps_url, business_status, primary_type,
    types, opening_hours, image_url, photo_name, photos, raw_data,
    created_at, updated_at
) VALUES (
    $1, $2, $3, $4, $5,
    $6, $7, $8, $9,
    $10, $11, $12, $13, $14,
    $15::jsonb, $16::jsonb, $17, $18, $19::jsonb, $20::jsonb,
    $21, $22
)
ON CONFLICT (google_place_id) DO UPDATE SET
    name = EXCLUDED.name,
    address = EXCLUDED.address,
    city_id = EXCLUDED.city_id,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    rating = EXCLUDED.rating,
    user_ratings_total = EXCLUDED.user_ratings_total,
    phone = EXCLUDED.phone,
    website = EXCLUDED.website,
    google_maps_url = EXCLUDED.google_maps_url,
    business_status = EXCLUDED.business_status,
    primary_type = EXCLUDED.primary_type,
    types = EXCLUDED.types,
    opening_hours = EXCLUDED.opening_hours,
    image_url = EXCLUDED.image_url,
    photo_name = EXCLUDED.photo_name,
    photos = EXCLUDED.photos,
    raw_data = EXCLUDED.raw_data,
    updated_at = EXCLUDED.updated_at
"""


def _normalize_url(url: str) -> str:
    return (
        url.replace("postgresql+asyncpg://", "postgresql://")
        .replace("postgresql+psycopg://", "postgresql://")
    )


def _json_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value)


async def clone_gaming_places(source_url: str, target_url: str) -> int:
    import asyncpg

    source = await asyncpg.connect(_normalize_url(source_url))
    target = await asyncpg.connect(_normalize_url(target_url))
    try:
        rows = await source.fetch("SELECT * FROM gaming_places ORDER BY name")
        if not rows:
            print("No gaming_places rows found in projectX.")
            return 0

        async with target.transaction():
            for row in rows:
                await target.execute(
                    GAMING_PLACES_UPSERT,
                    row["id"],
                    row["google_place_id"],
                    row["name"],
                    row["address"],
                    row["city_id"],
                    row["latitude"],
                    row["longitude"],
                    row["rating"],
                    row["user_ratings_total"],
                    row["phone"],
                    row["website"],
                    row["google_maps_url"],
                    row["business_status"],
                    row["primary_type"],
                    _json_value(row["types"]),
                    _json_value(row["opening_hours"]),
                    row["image_url"],
                    row["photo_name"],
                    _json_value(row["photos"]),
                    _json_value(row["raw_data"]),
                    row["created_at"],
                    row["updated_at"],
                )
        return len(rows)
    finally:
        await source.close()
        await target.close()


async def print_summary(source_url: str, target_url: str) -> None:
    import asyncpg

    source = await asyncpg.connect(_normalize_url(source_url))
    target = await asyncpg.connect(_normalize_url(target_url))
    try:
        source_tables = await source.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
        )
        print("\nprojectX tables:")
        for row in source_tables:
            count = await source.fetchval(f'SELECT COUNT(*) FROM "{row["tablename"]}"')
            print(f"  {row['tablename']}: {count}")

        target_count = await target.fetchval("SELECT COUNT(*) FROM gaming_places")
        print(f"\nPaythan gaming_places: {target_count}")
    finally:
        await source.close()
        await target.close()


async def main() -> None:
    source_url = os.environ.get("GAMING_PLACES_DATABASE_URL", DEFAULT_SOURCE)
    target_url = os.environ.get("DATABASE_URL", DEFAULT_TARGET)

    print(f"Source → {_normalize_url(source_url).split('@')[-1]}")
    print(f"Target → {_normalize_url(target_url).split('@')[-1]}")

    count = await clone_gaming_places(source_url, target_url)
    print(f"Cloned {count} gaming_places rows from projectX → Paythan")
    await print_summary(source_url, target_url)


if __name__ == "__main__":
    asyncio.run(main())