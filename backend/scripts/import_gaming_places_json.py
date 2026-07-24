#!/usr/bin/env python3
"""Import gaming_places from a JSON export into a target Postgres (e.g. Render).

Usage:
    cd backend
    source .venv/bin/activate

    # From local paythan (or any export JSON):
    DATABASE_URL='postgresql://USER:PASS@HOST/DB' \\
      python scripts/import_gaming_places_json.py data/local_gaming_places_export.json

Notes:
    - Accepts postgresql:// or postgresql+asyncpg:// URLs
    - Upserts on google_place_id (safe to re-run)
    - Creates schema tables first if needed: run alembic upgrade head against target first
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from uuid import UUID

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))
os.chdir(BACKEND_ROOT)

UPSERT = """
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


def _as_uuid(value):
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _as_dt(value):
    if value is None:
        return datetime.utcnow()
    if isinstance(value, datetime):
        return value
    # fromisoformat handles "2024-01-01T00:00:00+00:00"
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _json_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return json.dumps(value)


async def main() -> None:
    import asyncpg

    if len(sys.argv) < 2:
        print("Usage: DATABASE_URL=... python scripts/import_gaming_places_json.py <export.json>")
        sys.exit(2)

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"File not found: {path}")
        sys.exit(1)

    target_url = os.environ.get("DATABASE_URL") or os.environ.get("RENDER_DATABASE_URL")
    if not target_url:
        print("Set DATABASE_URL (or RENDER_DATABASE_URL) to the Render External Database URL")
        sys.exit(1)

    rows = json.loads(path.read_text())
    if not isinstance(rows, list):
        print("JSON must be a list of gaming_places objects")
        sys.exit(1)

    print(f"Loading {len(rows)} rows from {path}")
    print(f"Target → {_normalize_url(target_url).split('@')[-1]}")

    # Render free Postgres requires SSL
    conn = await asyncpg.connect(_normalize_url(target_url), ssl="require", timeout=30)
    try:
        # Ensure table exists (migrations should have created it)
        exists = await conn.fetchval(
            "SELECT to_regclass('public.gaming_places') IS NOT NULL"
        )
        if not exists:
            print("ERROR: gaming_places table missing on target. Run migrations first.")
            sys.exit(1)

        async with conn.transaction():
            for row in rows:
                await conn.execute(
                    UPSERT,
                    _as_uuid(row.get("id")),
                    row.get("google_place_id"),
                    row.get("name"),
                    row.get("address"),
                    _as_uuid(row.get("city_id")),
                    row.get("latitude"),
                    row.get("longitude"),
                    row.get("rating"),
                    row.get("user_ratings_total") or row.get("review_count") or 0,
                    row.get("phone"),
                    row.get("website"),
                    row.get("google_maps_url"),
                    row.get("business_status"),
                    row.get("primary_type"),
                    _json_value(row.get("types")),
                    _json_value(row.get("opening_hours")),
                    row.get("image_url"),
                    row.get("photo_name"),
                    _json_value(row.get("photos")),
                    _json_value(row.get("raw_data")),
                    _as_dt(row.get("created_at")),
                    _as_dt(row.get("updated_at")),
                )
        count = await conn.fetchval("SELECT COUNT(*) FROM gaming_places")
        print(f"Done. Target gaming_places count: {count}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
