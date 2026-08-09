"""Discovery list query — one static SQL, asyncpg Records → orjson."""

from __future__ import annotations

import base64
from typing import Any
from uuid import UUID

import asyncpg

# Static statement — NULL-guarded predicates so asyncpg can reuse the plan.
# $1 lat, $2 lng, $3 radius_m, $4 limit, $5 cursor_score, $6 cursor_id,
# $7 q, $8 min_rating, $9 available_now (bool or null), $10 amenities_mask,
# $11 sort ('distance'|'rating'|'relevance')

DISCOVERY_SQL = """
WITH params AS (
  SELECT
    $1::float8 AS lat,
    $2::float8 AS lng,
    $3::float8 AS radius_m,
    ST_SetSRID(ST_MakePoint($2::float8, $1::float8), 4326)::geography AS pt
)
SELECT
  c.id,
  c.name,
  coalesce(c.thumb_url, c.image_url) AS thumb_url,
  c.rating_score,
  c.review_count,
  c.available_now,
  c.amenities_mask,
  c.price_paise,
  c.latitude,
  c.longitude,
  ST_Distance(c.location, p.pt) AS distance_m,
  CASE
    WHEN $11::text = 'rating' THEN c.rating_score
    WHEN $11::text = 'relevance' THEN (
      0.5 * CASE WHEN $7::text IS NULL OR length(trim($7::text)) < 2 THEN 0
                 ELSE similarity(c.search_doc, lower($7::text)) END
      + 0.3 * (c.rating_score / 5.0)
      + 0.2 * exp(-ST_Distance(c.location, p.pt) / 3000.0)
    )
    ELSE ST_Distance(c.location, p.pt)
  END AS sort_value
FROM gaming_places c
CROSS JOIN params p
LEFT JOIN gaming_place_extensions e ON e.gaming_place_id = c.id
WHERE c.location IS NOT NULL
  AND ST_DWithin(c.location, p.pt, p.radius_m)
  AND (e.gaming_place_id IS NULL OR (e.is_deleted IS NOT TRUE AND e.is_active IS NOT FALSE))
  AND ($7::text IS NULL OR length(trim($7::text)) < 2 OR c.search_doc % lower($7::text))
  AND ($8::float8 IS NULL OR c.rating_score >= $8::float8)
  AND ($9::bool IS NULL OR c.available_now = $9::bool)
  AND ($10::int = 0 OR (c.amenities_mask & $10::int) = $10::int)
  AND (
    $5::float8 IS NULL
    OR (
      CASE
        WHEN $11::text = 'distance' THEN
          (ST_Distance(c.location, p.pt) > $5::float8
           OR (ST_Distance(c.location, p.pt) = $5::float8 AND c.id > $6::uuid))
        WHEN $11::text = 'rating' THEN
          (c.rating_score < $5::float8
           OR (c.rating_score = $5::float8 AND c.id > $6::uuid))
        ELSE
          (
            (
              0.5 * CASE WHEN $7::text IS NULL OR length(trim($7::text)) < 2 THEN 0
                         ELSE similarity(c.search_doc, lower($7::text)) END
              + 0.3 * (c.rating_score / 5.0)
              + 0.2 * exp(-ST_Distance(c.location, p.pt) / 3000.0)
            ) < $5::float8
            OR (
              (
                0.5 * CASE WHEN $7::text IS NULL OR length(trim($7::text)) < 2 THEN 0
                           ELSE similarity(c.search_doc, lower($7::text)) END
                + 0.3 * (c.rating_score / 5.0)
                + 0.2 * exp(-ST_Distance(c.location, p.pt) / 3000.0)
              ) = $5::float8 AND c.id > $6::uuid
            )
          )
      END
    )
  )
ORDER BY
  CASE WHEN $11::text = 'distance' THEN ST_Distance(c.location, p.pt) END ASC NULLS LAST,
  CASE WHEN $11::text = 'rating' THEN c.rating_score END DESC NULLS LAST,
  CASE WHEN $11::text = 'relevance' THEN (
    0.5 * CASE WHEN $7::text IS NULL OR length(trim($7::text)) < 2 THEN 0
               ELSE similarity(c.search_doc, lower($7::text)) END
    + 0.3 * (c.rating_score / 5.0)
    + 0.2 * exp(-ST_Distance(c.location, p.pt) / 3000.0)
  ) END DESC NULLS LAST,
  c.id ASC
LIMIT $4::int
"""

# Appendix A fallback when PostGIS geography column missing
DISCOVERY_SQL_BBOX = """
SELECT * FROM (
  SELECT
    c.id,
    c.name,
    coalesce(c.thumb_url, c.image_url) AS thumb_url,
    coalesce(c.rating_score, coalesce(c.rating, 0)) AS rating_score,
    coalesce(c.review_count, coalesce(c.user_ratings_total, 0)) AS review_count,
    coalesce(c.available_now, false) AS available_now,
    coalesce(c.amenities_mask, 0) AS amenities_mask,
    c.price_paise,
    c.latitude,
    c.longitude,
    (6371000 * acos(LEAST(1.0, GREATEST(-1.0,
        cos(radians($1)) * cos(radians(c.latitude))
        * cos(radians(c.longitude) - radians($2))
        + sin(radians($1)) * sin(radians(c.latitude))
    )))) AS distance_m,
    (6371000 * acos(LEAST(1.0, GREATEST(-1.0,
        cos(radians($1)) * cos(radians(c.latitude))
        * cos(radians(c.longitude) - radians($2))
        + sin(radians($1)) * sin(radians(c.latitude))
    )))) AS sort_value
  FROM gaming_places c
  LEFT JOIN gaming_place_extensions e ON e.gaming_place_id = c.id
  WHERE c.latitude IS NOT NULL AND c.longitude IS NOT NULL
    AND c.latitude BETWEEN ($1 - ($3 / 111320.0)) AND ($1 + ($3 / 111320.0))
    AND c.longitude BETWEEN ($2 - ($3 / (111320.0 * cos(radians($1)))))
                        AND ($2 + ($3 / (111320.0 * cos(radians($1)))))
    AND (e.gaming_place_id IS NULL OR (e.is_deleted IS NOT TRUE AND e.is_active IS NOT FALSE))
    AND ($7::text IS NULL OR length(trim($7::text)) < 2
         OR lower(c.name) LIKE '%' || lower($7::text) || '%'
         OR lower(coalesce(c.address,'')) LIKE '%' || lower($7::text) || '%')
    AND ($8::float8 IS NULL OR coalesce(c.rating_score, coalesce(c.rating,0)) >= $8::float8)
    AND ($9::bool IS NULL OR coalesce(c.available_now, false) = $9::bool)
    AND ($10::int = 0 OR (coalesce(c.amenities_mask,0) & $10::int) = $10::int)
) AS nearby
WHERE distance_m <= $3
  AND (
    $5::float8 IS NULL
    OR distance_m > $5::float8
    OR (distance_m = $5::float8 AND id > $6::uuid)
  )
ORDER BY distance_m ASC, id ASC
LIMIT $4::int
"""


def encode_cursor(sort_value: float, centre_id: UUID | str) -> str:
    raw = f"{sort_value}:{centre_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def decode_cursor(cursor: str | None) -> tuple[float | None, UUID | None]:
    if not cursor:
        return None, None
    pad = "=" * (-len(cursor) % 4)
    try:
        raw = base64.urlsafe_b64decode(cursor + pad).decode()
        score_s, id_s = raw.split(":", 1)
        return float(score_s), UUID(id_s)
    except Exception:
        return None, None


def record_to_item(row: asyncpg.Record) -> dict[str, Any]:
    return {
        "id": str(row["id"]),
        "name": row["name"],
        "thumb_url": row["thumb_url"],
        "rating_score": round(float(row["rating_score"] or 0), 2),
        "review_count": int(row["review_count"] or 0),
        "available_now": bool(row["available_now"]),
        "amenities_mask": int(row["amenities_mask"] or 0),
        "price_paise": row["price_paise"],
        "distance_m": int(round(float(row["distance_m"]))),
        "lat": float(row["latitude"]) if row["latitude"] is not None else None,
        "lng": float(row["longitude"]) if row["longitude"] is not None else None,
    }


async def fetch_centres(
    conn: asyncpg.Connection,
    *,
    lat: float,
    lng: float,
    radius_m: int,
    limit: int,
    cursor: str | None,
    q: str | None,
    min_rating: float | None,
    available_now: bool | None,
    amenities_mask: int,
    sort: str,
    use_postgis: bool = True,
) -> tuple[list[dict[str, Any]], str | None]:
    cursor_score, cursor_id = decode_cursor(cursor)
    q_param = q.strip() if q and len(q.strip()) >= 2 else None
    args = [
        lat,
        lng,
        float(radius_m),
        limit + 1,  # fetch one extra for has_more
        cursor_score,
        cursor_id,
        q_param,
        min_rating,
        available_now,
        int(amenities_mask or 0),
        sort,
    ]
    sql = DISCOVERY_SQL if use_postgis else DISCOVERY_SQL_BBOX
    try:
        rows = await conn.fetch(sql, *args)
    except asyncpg.UndefinedColumnError:
        # migration not applied / no location column
        rows = await conn.fetch(DISCOVERY_SQL_BBOX, *args)
    except asyncpg.UndefinedFunctionError:
        rows = await conn.fetch(DISCOVERY_SQL_BBOX, *args)

    items = [record_to_item(r) for r in rows[:limit]]
    next_cursor = None
    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = encode_cursor(float(last["sort_value"]), last["id"])
    return items, next_cursor
