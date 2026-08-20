# Dev error backlog (auto-refreshed)

Last probe: **2026-08-20 16:55 UTC**  
Target: `https://gamer-circle-api.onrender.com`  
Health version field: ``  
Summary: **15 FAIL** · 0 OK · 0 auth-gated

## Open failures (fix these)

| # | Code | Method | Path | Message | Likely fix |
|---|------|--------|------|---------|------------|
| 1 | 503 | `GET` | `/health` |  | Investigate response + recent sit deploy |
| 2 | 503 | `GET` | `/api/v1/home` |  | Investigate response + recent sit deploy |
| 3 | 503 | `GET` | `/api/v1/feed/ranked` |  | Investigate response + recent sit deploy |
| 4 | 429 | `GET` | `/api/v1/reels/feed?page=1&limit=1` | <!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta htt | Investigate response + recent sit deploy |
| 5 | 429 | `GET` | `/api/v1/geo/nearby-parlors?lat=28.6139&lng=77.209&radius_km=30` | <!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta htt | Investigate response + recent sit deploy |
| 6 | 429 | `GET` | `/api/v1/search?q=vr&limit=5` | <!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta htt | Investigate response + recent sit deploy |
| 7 | 429 | `GET` | `/api/v1/search/smart?q=vr&limit=5` | <!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta htt | Investigate response + recent sit deploy |
| 8 | 429 | `GET` | `/api/v1/discovery/centres?lat=28.6139&lng=77.209&radius_km=20` | <!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta htt | Investigate response + recent sit deploy |
| 9 | 429 | `GET` | `/api/v1/parlors/316a4e1c-2882-4ee1-87f6-e007e042798d/availability?date=2026-08-10&station_type=PC` | <!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta htt | Investigate response + recent sit deploy |
| 10 | 429 | `GET` | `/api/v1/clubs/316a4e1c-2882-4ee1-87f6-e007e042798d/availability?date=2026-08-10&station_type=PC` | <!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta htt | Investigate response + recent sit deploy |
| 11 | 429 | `POST` | `/api/v1/bookings/hold` | <!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta htt | Investigate response + recent sit deploy |
| 12 | 429 | `POST` | `/api/v1/bookings/v2` | <!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta htt | Investigate response + recent sit deploy |
| 13 | 429 | `GET` | `/api/v1/conversations` | <!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta htt | Investigate response + recent sit deploy |
| 14 | 429 | `GET` | `/api/v1/feed` | <!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta htt | Investigate response + recent sit deploy |
| 15 | 429 | `POST` | `/api/v1/posts` | <!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title><meta htt | Investigate response + recent sit deploy |

## Known root causes (checklist)

1. **[P0] Render API stuck on old deploy** — `/health` version not matching `sit`. Dashboard → gamer-circle-api → Manual Deploy → Clear build cache (branch `sit`).
2. **[P0] Flutter path aliases** — use `/parlors/{id}/availability` (not `/clubs/...`); `ApiCompatInterceptor` strips double `/api/v1`.
3. **[P1] `/reels/feed` 500** — soft-fail empty feed if DB schema missing (deploy required).
4. **[P1] `/search/smart` 404** — alias added; Flutter falls back to `/search`.
5. **[P1] `/bookings/hold` 405** — missing on old deploy; after redeploy should return 401/422.
6. **[P1] `/discovery/centres` 404** — missing on old deploy; ships with `sit`.

## Auth-gated (OK without token)


## Passing public probes


