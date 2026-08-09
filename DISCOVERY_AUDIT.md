# DISCOVERY_AUDIT.md — Phase 0

> Audit only. **No schema/API/UI changes made.**  
> Spec: Nearby gaming centres · List · Search · Filters (Distance, Rating, Available now)  
> Live API probed: `https://gamer-circle-api.onrender.com` (`git_sha=774af3d`) · Date: 2026-08-09

---

## 1. Canonical table name (substitute for “clubs” in later phases)

| Spec name | Real table | Notes |
|---|---|---|
| **clubs** | **`gaming_places`** | Canonical discovery catalog. Synced from external ProjectX dump. |
| overlay | `gaming_place_extensions` | Owner, soft-delete, prices, follower/post counts, verified flags. |
| legacy | `parlors` | Older social/tournament venue table with PostGIS `location` + GiST. **Not** the discovery list source today. |

### `gaming_places` columns (from model + migration `009a`)

| Column | Type | Indexed? |
|---|---|---|
| `id` | UUID PK | PK |
| `google_place_id` | String(255) unique | `ix_gaming_places_google_place_id` |
| `name` | String(500) | no |
| `address` | Text | no |
| `city_id` | UUID | `ix_gaming_places_city_id` |
| `latitude` / `longitude` | Float nullable | **no geo index** |
| `rating` | Float nullable | no (Google-sourced) |
| `user_ratings_total` | Integer nullable | no |
| `phone`, `website`, `google_maps_url` | String | no |
| `business_status`, `primary_type` | String | no |
| `types`, `opening_hours`, `photos`, `raw_data` | JSONB | no |
| `image_url`, `photo_name` | String | no |
| `image_asset_id` | UUID FK → media_assets (016) | FK only |
| `created_at`, `updated_at` | timestamptz | no |

### Missing vs Discovery Phase 1 target (on `gaming_places` or overlay)

| Spec column / index | Present? |
|---|---|
| `location geography(Point,4326)` + GiST | **No** — only float lat/lng |
| `available_now` boolean + partial index | **No** |
| `rating_score` Bayesian precompute | **No** — uses Google `rating` or live AVG from `parlour_ratings` |
| `search_doc` + `pg_trgm` GIN | **No** — text search is `ILIKE '%q%'` |
| `amenities_mask` bitmask | **No** — amenities only as ad-hoc strings on detail payloads |
| Money in integer paise on list card | **Partial** — booking ledger has `*_paise`; extension still uses `Numeric(10,2)` `price_per_hour` |
| Keyset cursor pagination | **No** — `OFFSET` via `page` |

### Related tables (for Celery denorm later)

| Table | Role |
|---|---|
| `gaming_slots` / `gaming_bookings` / `booking_holds` / `parlor_stations` / `parlor_hours` | Availability source |
| `parlour_ratings` | User reviews (`rating` Numeric 3,2; unique per user×place) |
| `parlour_offers` | Promo text / discounts for cards |

---

## 2. PostGIS & pg_trgm availability

| Extension | In repo? | On live Render? | Usable for discovery today? |
|---|---|---|---|
| **PostGIS** | Yes — `CREATE EXTENSION IF NOT EXISTS postgis` in alembic `005` + `scripts/render-start.sh` (best-effort) | **Likely yes** (start script + `/ready` DB OK). Not queried with `SELECT PostGIS_Version()` from this agent (no SQL shell). | **Not for list path.** `gaming_places` has **no** stored geography column / GiST. `GeoService._postgis_nearby_rows` builds `ST_MakePoint(longitude, latitude)::geography` per row → even with PostGIS this is effectively a **seq-scan + filter**, not KNN/`<->` index scan. Hot path `ParlorRepository._distance_rows_sql` uses **SQL Haversine**, not `ST_DWithin`. |
| **pg_trgm** | **Not referenced** anywhere in migrations or app code | Unknown / almost certainly unused | Text search = `ILIKE` / `contains` → seq scan risk |

**Phase 1 decision:** Prefer full PostGIS path (add `location` geography + GiST on `gaming_places`). Appendix A (bbox + haversine) only if Render `CREATE EXTENSION postgis` fails at migrate time — verify in Phase 1 with `EXPLAIN` before proceeding.

Legacy note: `parlors.location` already has GiST (`006_add_gist_index_parlors_location.py`) but discovery reads **`gaming_places`**, not `parlors`.

---

## 3. Existing discovery / search endpoints

Mounted under `/api/v1` from `backend/app/main.py` (domains layout — **no** `app/api/v1/` package yet; Phase 3 file `app/api/v1/discovery.py` would be **new** or should be `app/domains/discovery/` to match repo convention).

| Method | Path | File | Behavior today | Spec gap |
|---|---|---|---|---|
| GET | `/geo/nearby-parlors` | `domains/geo/router.py` → `GeoService` → `ParlorRepository` | Lat/lng/radius/game_type/limit; Redis cache 120s; Pydantic response | Haversine / non-indexed PostGIS; no keyset; no available_now |
| GET | `/geo/search-parlors` | same | q, min_rating, open_now, city, state, game_type, **page/limit OFFSET** | ILIKE; open_now computed in Python from `opening_hours`; multi-query |
| GET | `/geo/nearby-tournaments` | same | PostGIS-ish for tournaments | Out of discovery list scope |
| GET | `/home` | `domains/home/router.py` | nearby + quick_picks + cities + posts | Aggregate home, not pure list endpoint |
| GET | `/home/nearby`, `/home/quick-picks`, `/cities` | same | Sub-feeds | — |
| GET | `/search` | `domains/search/router.py` | parlor+tournament ILIKE | Not geo-aware |
| GET | `/parlors/{id}/ratings` | gaming_booking | Ratings summary | Detail, not list |

**Serialization today:** SQLAlchemy ORM → Pydantic → FastAPI JSON. **No** raw asyncpg pool, **no** `ORJSONResponse`, **no** `GZipMiddleware` on this path.

**Queries per nearby/search request today:** ≥2 (distance id list + hydrate `GamingPlace` (+ extension via `_to_view`)). Violates “one request = one SQL”.

**Redis today:** key `geo:parlors:{lat2}:{lng2}:{radius}:{game_type}` — coarse lat/lng round, **not** geohash6; stores JSON dicts, not orjson bytes; no stampede lock; no ETag/304.

**Celery today:** beat has recommendation + booking holds + club_ops rollups. **No** `refresh_availability` / `refresh_rating_scores` / `search_doc` trigger.

---

## 4. Flutter files — modify vs create

### No `lib/features/discovery/` yet — **CREATE** (Phase 5–6)

| New path | Purpose |
|---|---|
| `lib/features/discovery/data/discovery_api.dart` | Dio client for single discovery endpoint |
| `lib/features/discovery/data/discovery_repository.dart` | Cursor + stale-while-revalidate |
| `lib/features/discovery/data/centre_summary.dart` | Small hand-written DTO |
| `lib/features/discovery/presentation/discovery_page.dart` | List + filters |
| `lib/features/discovery/presentation/centre_card.dart` | Fixed-height card |
| `lib/features/discovery/presentation/filter_sheet.dart` | Distance / rating / available now / amenities |
| `lib/features/discovery/presentation/filter_state.dart` | Immutable `FilterState` |
| `lib/core/amenities.dart` | Bitmask enum (mirror backend) |

### Existing — **MODIFY** (wire into new module / keep as callers)

| File | Role today |
|---|---|
| `lib/features/home/presentation/home_screen.dart` + `nearby_parlors_section.dart` | Home nearby rail |
| `lib/features/home/presentation/widgets/parlor_filter_chips.dart` | Distance / 4+ / Open Now / BGMI chips |
| `lib/features/home/providers/home_filters_provider.dart` | Radius enum 2–20 km |
| `lib/features/home/providers/parlor_search_provider.dart` | Search filters state |
| `lib/features/home/data/home_repository.dart` | Home API |
| `lib/features/parlors/data/parlor_search_repository.dart` | Calls `/geo/search-parlors` with page |
| `lib/features/parlors/presentation/search_results_screen.dart` / `search_input_screen.dart` | Search UI |
| `lib/features/map/presentation/discover_screen.dart` | Map/list toggle → `/geo/nearby-parlors` |
| `lib/core/data/social_remote_datasource.dart` | `nearbyParlors` / search helpers |
| `lib/shared/models/nearby_parlor.dart`, `parlour_search.dart` | List DTOs (larger than 10-field target) |
| `lib/shared/widgets/parlour_list_card.dart` | Card (not fixed `itemExtent`) |
| `lib/core/providers/location_provider.dart` + `features/location/**` | GPS — has geolocator; needs last-known → medium accuracy + 150 m stream pattern |

### Dependencies already present

- `geolocator`, `cached_network_image`, Riverpod, Dio  
- **Missing for Phase 5 local cache:** Hive or Isar (not in `pubspec.yaml`)

---

## 5. Current row counts (live + local)

| Entity | Count | Source |
|---|---|---|
| Centres (`gaming_places` / admin “parlors”) | **141** | `GET /api/v1/admin/stats` → `parlors: 141`; local export `backend/data/local_gaming_places_export.json` also 141 |
| Users | **2** | admin stats |
| Bookings (`gaming_bookings`) | **1** | admin stats (`bookings: 1`); admin list returned `total: 0` for empty page filter — treat **1** as authoritative from stats |
| Reviews (`parlour_ratings`) | **~0** seeded | Sample `GET /parlors/{id}/ratings` → `total_reviews: 0`; no admin aggregate; assume **near-zero** until Celery/seed |
| Tournaments / posts | 0 / 0 | admin stats |
| Nearby @ Delhi 5 km | 5 returned (limit=5); home nearby=10 | live `/geo/nearby-parlors`, `/home` |

Direct `SELECT count(*)` / `EXPLAIN` against Render Postgres was **not** possible from this agent (no DB URL / shell). Phase 1 must run EXPLAIN on the Render DB or a local PostGIS clone.

---

## 6. Gap summary vs Phase 7 targets

| Spec requirement | Current state |
|---|---|
| p95 list < 80 ms uncached | Unlikely — Haversine/subquery + ORM hydrate + Pydantic; no GiST |
| Payload < 15 KB gzipped / 20 items | No gzip middleware; fat Pydantic cards with address/images |
| 1 SQL per request | **No** (≥2) |
| Zero per-request geo math in Python | **No** — Python Haversine fallback + `is_open_now` parsing |
| Denormalized `available_now` | **No** — “Open Now” = opening_hours JSON parse |
| Keyset cursor | **No** — OFFSET `page` |
| Redis geohash + orjson bytes + ETag | **No** — lat2 cache + JSON strings |
| Flutter fixed `itemExtent` + discovery feature | **No** dedicated module |

---

## 7. Naming map for later phases

When the spec says **clubs**, implement against **`gaming_places`** (join `gaming_place_extensions` only if needed for list fields — prefer denormalized columns **on** `gaming_places` or a thin read-model table to keep **one** query).

Suggested backend layout (repo convention):  
`backend/app/domains/discovery/{router,service,cache}.py` + `app/tasks/discovery.py`  
(rather than new top-level `app/api/v1/` unless you explicitly want that package).

---

## 8. Phase 0 stop

**Audit complete. No code or migrations changed.**

Awaiting approval to start **Phase 1 — Database: schema, denormalized read columns, indexes** (`alembic revision -m "discovery_read_model"`), substituting **`gaming_places`** for `clubs` everywhere.
