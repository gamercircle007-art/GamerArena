# Dev error backlog (auto-refreshed)

Last probe: **2026-08-21 08:20 UTC**  
Target: `https://gamer-circle-api.onrender.com`  
Health version field: `The read operation timed out`  
Summary: **10 FAIL** · 1 OK · 4 auth-gated

## Open failures (fix these)

| # | Code | Method | Path | Message | Likely fix |
|---|------|--------|------|---------|------------|
| 1 | 0 | `GET` | `/health` | The read operation timed out | Network / cold start — retry |
| 2 | 0 | `GET` | `/api/v1/home` | The read operation timed out | Network / cold start — retry |
| 3 | 500 | `GET` | `/api/v1/reels/feed?page=1&limit=1` | An unexpected error occurred | Deploy soft-fail feed; run alembic for reels tables |
| 4 | 500 | `GET` | `/api/v1/geo/nearby-parlors?lat=28.6139&lng=77.209&radius_km=30` | An unexpected error occurred | Investigate response + recent sit deploy |
| 5 | 500 | `GET` | `/api/v1/search?q=vr&limit=5` | An unexpected error occurred | Investigate response + recent sit deploy |
| 6 | 404 | `GET` | `/api/v1/search/smart?q=vr&limit=5` | Not Found | Deploy /search/smart alias; app falls back to /search |
| 7 | 404 | `GET` | `/api/v1/discovery/centres?lat=28.6139&lng=77.209&radius_km=20` | Not Found | Redeploy sit (discovery router missing on live) |
| 8 | 500 | `GET` | `/api/v1/parlors/316a4e1c-2882-4ee1-87f6-e007e042798d/availability?date=2026-08-10&station_type=PC` | An unexpected error occurred | Investigate response + recent sit deploy |
| 9 | 404 | `GET` | `/api/v1/clubs/316a4e1c-2882-4ee1-87f6-e007e042798d/availability?date=2026-08-10&station_type=PC` | Not Found | Redeploy sit OR client uses /parlors (compat interceptor) |
| 10 | 405 | `POST` | `/api/v1/bookings/hold` | Method Not Allowed | Redeploy sit — hold route not mounted; shadowed by GET /bookings/{id} |

## Known root causes (checklist)

1. **[P0] Render API stuck on old deploy** — `/health` version not matching `sit`. Dashboard → gamer-circle-api → Manual Deploy → Clear build cache (branch `sit`).
2. **[P0] Flutter path aliases** — use `/parlors/{id}/availability` (not `/clubs/...`); `ApiCompatInterceptor` strips double `/api/v1`.
3. **[P1] `/reels/feed` 500** — soft-fail empty feed if DB schema missing (deploy required).
4. **[P1] `/search/smart` 404** — alias added; Flutter falls back to `/search`.
5. **[P1] `/bookings/hold` 405** — missing on old deploy; after redeploy should return 401/422.
6. **[P1] `/discovery/centres` 404** — missing on old deploy; ships with `sit`.

## Auth-gated (OK without token)

- `401` `POST` `/api/v1/bookings/v2`
- `401` `GET` `/api/v1/conversations`
- `401` `GET` `/api/v1/feed`
- `401` `POST` `/api/v1/posts`

## Passing public probes

- `200` `GET` `/api/v1/feed/ranked`

