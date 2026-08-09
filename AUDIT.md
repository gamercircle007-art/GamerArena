# AUDIT.md — Phase-0 / Master Build Plan Step 1

**Scope:** factual audit of `/workspace` (GamerArena / Paythan / GamerCircle monorepo).  
**Rule:** no application/schema changes in this step — facts only.  
**Date:** 2026-08-09  
**Repo HEAD audited:** `sit` @ `474c9a1` (includes discovery + booking-lock merges).  
**Live API probed:** `https://gamer-circle-api.onrender.com` → `/ready` reports `git_sha=774af3d` (ancestor of HEAD; **pre-discovery / pre-024**).

> Spec vocabulary uses `clubs` / `resources` / `bookings`. This audit substitutes **real** table names below.

---

## 0. Inventory note — “52 Master Build Plan steps”

No file named `MASTER_BUILD_PLAN.md` (or equivalent numbered 1–52 list) exists in the repo.

**Closest in-repo 52-item inventory** (used for §7):

| Block | Source | Count |
|---|---|---|
| A | `docs/SPEC_COMPLETION_CHECKLIST.md` leaf checkboxes | **29** |
| B | Discovery module phases 0–7 (`DISCOVERY_AUDIT.md` + PR #6) | **8** |
| C | Availability & Booking Lock phases 0–8 (`AVAILABILITY_AUDIT.md` + PR #8) | **9** |
| D | Club Management phases 0–5 (`CLUB_MANAGEMENT_BUILD.md`; Phase 2.5 folded into Phase 2) | **6** |
| | **Total** | **52** |

If a separate external Master Build Plan differs, remap using the evidence rows in §7.

---

## 1. Spec term → real table names

| Spec term | Real table | Notes |
|---|---|---|
| club / centre / parlor (discovery) | **`gaming_places`** | Canonical venue catalog. Models: `backend/app/domains/gaming_place/models.py` |
| club overlay (owner, soft-delete, ₹/hr) | **`gaming_place_extensions`** | `owner_id`, `price_per_hour` Numeric, `is_deleted` / `deleted_at` |
| club (legacy social/tournament) | **`parlors`** | Older PostGIS venue (`parlors.location` GiST via migration `006`). Not discovery list source |
| resource (physical unit) | **`club_resources`** | Per-PC/console/seat; migration `022` |
| zone | **`club_zones`** | Groups resources; migration `022` |
| resource (capacity bucket) | **`parlor_stations`** | Aggregate `total_count` per `station_type`; migration `021` |
| booking (customer / parlor) | **`gaming_bookings`** | Primary booking row; FK `parlour_id` → `gaming_places.id` |
| hold | **`booking_holds`** + `gaming_bookings.hold_expires_at` | Also lock rows in `booking_unit_locks` (024) |
| lock / exclusion row | **`booking_unit_locks`** | GiST `EXCLUDE` correctness layer (024) |
| slot grid | **`gaming_slots`** | Materialized hourly inventory |
| review | **`parlour_ratings`** | User ratings for places |
| user | **`users`** | Roles: `user` / `parlor_owner` / `admin` (`UserRole` enum) |
| tournament booking | **`bookings`** | Separate product (`domains/tournament`); not parlor time-grid |
| payment ledger | **`payment_ledger`** | Cashfree money movements (paise) |
| webhook idempotency | **`webhook_events`** | Unique `event_id` |
| pricing / promos (club-ops) | **`club_pricing_rules`**, **`club_promotions`** | Migration `022` |
| customers (club CRM) | **`club_customers`**, **`club_customer_notes`** | Migration `022` |
| occupancy rollups | **`club_occupancy_rollups`** | Celery-written; migration `022` |

### Key columns (abbreviated)

**`gaming_places`:** `id`, `name`, `address`, `city_id`, `latitude`/`longitude` (Float), discovery denorm (`available_now`, `rating_score`, `amenities_mask`, `price_paise`, `thumb_url`, `search_doc`, `review_count`), PG-only `location geography(Point,4326)` (023).

**`gaming_bookings`:** `id`, `booking_ref`, `user_id`, `parlour_id`, `slot_id`, `resource_id`, `slot_date`/`start_time`/`end_time`, `during_start`/`during_end` (+ PG `during tstzrange`), `booking_status`/`payment_status` (String), `amount_paise`/`commission_paise`, `idempotency_key`, `hold_expires_at`, `station_type`/`units`/`duration_hours`, legacy `Numeric(10,2)` price fields.

**`club_resources`:** `parlor_id`, `zone_id`, `resource_type`, `name`, `status`, `specs`, `hourly_rate_override`, `layout_x`/`layout_y`, `is_active`.

**`booking_unit_locks`:** `booking_id`, `parlor_id`, `station_type`, `unit_index`, `resource_id`, `during_start`/`during_end`, `is_active` + PG `during` + EXCLUDE constraints.

---

## 2. Extensions — postgis, btree_gist, pg_trgm

| Extension | In migrations / scripts | Creatable locally | On live Render (inferred) |
|---|---|---|---|
| **postgis** | `005` (`CREATE EXTENSION IF NOT EXISTS postgis`); `023` again; `scripts/render-start.sh` best-effort `CREATE EXTENSION postgis` | Yes — `docker-compose.yml` image `postgis/postgis:16-3.4-alpine` | Likely present (start script + legacy parlor GiST). Live API at `774af3d` may **not** have run `023` yet |
| **pg_trgm** | **`023_discovery_read_model.py` only** (`CREATE EXTENSION IF NOT EXISTS pg_trgm`) | Yes if Postgres allows (superuser / allowed extensions) | Unknown until `023` applied on Render |
| **btree_gist** | **`024_booking_lock_ranges.py` only** (`CREATE EXTENSION IF NOT EXISTS btree_gist`) — required for scalar `=` in GiST EXCLUDE | Yes on standard PG | Unknown until `024` applied on Render |

**Dockerfile** (`backend/Dockerfile`): Python 3.12 slim — **does not** install Postgres extensions (DB is external Render Postgres / compose PostGIS image).

**render.yaml:** Postgres 16 free plan `gamer-circle-db` — no extension list; extensions created via alembic / start script.

**Ops gap:** Live `/ready` `git_sha=774af3d` is before PRs #6/#8. Until deploy + `alembic upgrade head`, live DB may lack `023`/`024` columns and extensions.

---

## 3. Booking overlap check — EXCLUDE vs SELECT-then-INSERT

### Primary customer path (hold / v2) — EXCLUDE in place (repo)

| Piece | Path / fact |
|---|---|
| Migration | `backend/alembic/versions/024_booking_lock_ranges.py` |
| Constraints | `excl_booking_unit_locks_overlap`, `excl_booking_unit_locks_resource`, `excl_gaming_bookings_resource_during` |
| App layer | `backend/app/domains/gaming_booking/lock_service.py` — insert locks, catch SQLSTATE `23P01`; comment: “Never SELECT-check-then-INSERT for correctness” |
| APIs | `POST /bookings/hold`, `POST /bookings/{id}/release`, `POST /bookings/{id}/pay`, `POST /bookings/v2` → `availability_router.py` → `LockService` / `AvailabilityService.create_booking_v2` |
| Hold TTL | `HOLD_MINUTES = 8` in `lock_service.py` |

### Remaining TOCTOU / non-EXCLUDE paths

| Path | File | Mechanism | EXCLUDE? |
|---|---|---|---|
| **Legacy parlor create** | `domains/gaming_booking/service.py` `create_booking` | Redis `SET NX` + `SELECT GamingSlot … FOR UPDATE` + counter bump | **No** — does not write `booking_unit_locks` |
| **Walk-in** | `domains/club_ops/service.py` `create_walk_in` | App-level free-resource pick + plain `INSERT gaming_bookings` | **No** — no `LockService` / unit-lock insert |
| **Tournament book** | `domains/booking/service.py` `book_slot` | Redis NX + `SELECT Tournament … FOR UPDATE` + counter | **No** — table `bookings`, out of parlor EXCLUDE scope |

`compute_availability` still exists for **read** grids (`AvailabilityService.compute_availability`); correctness for new holds is EXCLUDE insert, not the SELECT.

---

## 4. Flutter state management

| Item | Fact |
|---|---|
| Primary package | **`flutter_riverpod: ^2.5.1`** + `riverpod_annotation: ^2.3.5` (`frontend/gamer_circle/pubspec.yaml`) |
| Codegen | `riverpod_generator`, `riverpod_lint` (dev) |
| **Not present** | No `flutter_bloc`, no `get`/`GetX`, no `provider` package (only `path_provider`) |
| Pattern | Riverpod throughout (`Provider`, `FutureProvider`, `StateProvider`, `NotifierProvider`, `AsyncNotifier` / `FamilyAsyncNotifier`). AGENT.md §6: AsyncNotifier for async state |
| Booking | `gaming_booking_provider.dart` (Notifier) + `SlotGridController` (presentation helper) |
| Discovery | Riverpod in `features/discovery/` |

**Do not add a second state-management framework** — Riverpod is established.

---

## 5. Angular admin

| Item | Fact |
|---|---|
| Path | `admin-microservice-complete/frontend/` |
| package.json | `@angular/core` **`^21.2.0`** |
| package-lock | `@angular/core` **`21.2.17`** (resolved) |
| CLI / build | `@angular/cli` / `@angular/build` `^21.2.17` |
| Bootstrap | `bootstrapApplication(App, appConfig)` in `src/main.ts` |
| Components | **`standalone: true`** (41 occurrences); **0** `NgModule` under `src/` |
| Pattern | Standalone + `inject()` (per AGENT.md); routes in `app.routes.ts` |
| RBAC UI | `core/guards/auth.guard.ts`, `role.guard.ts` |
| Club oversight | `features/club-management/club-management-list.component.ts` |
| Deploy | `render.yaml` static site `gamer-circle-admin` |

---

## 6. Uvicorn workers (WS Pub/Sub implications)

| Source | Value |
|---|---|
| `render.yaml` | `WEB_CONCURRENCY=1`; default `startCommand` = single `uvicorn` **without** `--workers` when `USE_FULL_BOOT=0` (current default) |
| `scripts/render-start.sh` | `WORKERS="${WEB_CONCURRENCY:-1}"` then `uvicorn … --workers "${WORKERS}"` |
| `backend/Dockerfile` production | CMD `scripts/render-start.sh` |
| `.env.example` / compose | Single process; **no Celery worker/beat service** in `docker-compose.yml` or `render.yaml` |

**Conclusion:** Production blueprint is **single worker**. Availability WS (`/api/v1/ws/clubs/{id}/availability`) still publishes via Redis (`ws:*` / `LockService` fan-out) so multi-worker remains safe if `WEB_CONCURRENCY` is raised later.

**Celery:** beat schedule exists in `app/tasks/celery_app.py` (holds 30s, discovery refresh, rollups, reconcile). **No** Celery process declared in Render/compose blueprints — jobs run only if operated outside these files.

---

## 7. Master Build Plan steps 1–52 — status

Status values: `done` | `partial` | `not_started` | `n/a`  
Evidence is one line (file / feature / live fact).

### A. Cashfree + Slots checklist (`docs/SPEC_COMPLETION_CHECKLIST.md`) — steps 1–29

| # | Step (checklist leaf) | Status | Evidence |
|---|---|---|---|
| 1 | Code map `docs/PHASE0_CODE_MAP.md` | done | File present |
| 2 | Migration `021` stations/hours/holds/ledger/webhooks | done | `alembic/versions/021_cashfree_slots_onboarding.py` |
| 3 | GamingBooking v2 columns (paise, cf, idempotency, hold) | done | `gaming_booking/models.py` |
| 4 | `GET /parlors/{id}/availability` | done | `availability_router.py` |
| 5 | `GET /parlors/{id}/station-types` | done | `availability_router.py` |
| 6 | `POST /bookings/v2` + Idempotency-Key + holds | done | `availability_router.py` + `LockService` (EXCLUDE) |
| 7 | `GET /bookings/{id}/status` + Cashfree poll | done | `availability_router.py` |
| 8 | Materialized fallback slots (`slot_engine`) | done | `gaming_booking/slot_engine.py` |
| 9 | Celery expire / sweep / nightly reconciliation | partial | Code: 30s sweep in `celery_app.py`; **no** Celery service in `render.yaml` |
| 10 | `cashfree_client.py` create/get + webhook HMAC | done | `domains/payments/cashfree_client.py` |
| 11 | `POST /payments/cashfree/bookings/{id}/order` | done | `payments/router.py` |
| 12 | `POST /payments/webhooks/cashfree` | done | `payments/router.py` + `webhook_events` |
| 13 | Mock mode when keys missing | done | Live `/ready`: `cashfree_configured: false` |
| 14 | Payment ledger rows on confirm | done | `payment_ledger` model + confirm path |
| 15 | Live sandbox UPI E2E | not_started | Live: `cashfree_configured: false`; checklist unchecked |
| 16 | Full refund Cashfree API path | partial | `auto_refund` enqueue in `lock_service.py`; checklist still open for full provider path |
| 17 | Flutter station chips / duration / units / price bar | done | `features/booking/` + parlor detail |
| 18 | Book Now → `/bookings/v2` → status poll | done | `gaming_booking_repository.dart` / status screen |
| 19 | My Bookings wired | done | `gaming_my_bookings_screen.dart` |
| 20 | Official Cashfree Flutter SDK UI | not_started | Checklist unchecked; mock/pay-at-parlor only |
| 21 | Angular `/parlors/onboarding` wizard | done | `parlor-onboarding.component.ts` |
| 22 | Full 5-step parlor create + 2FA + refund drawers | partial | Onboarding exists; checklist marks rest partial |
| 23 | Server-side amount (paise) for v2 | partial | `amount_paise` / `hourly_price_paise` used; legacy `Numeric(10,2)` still on same booking row |
| 24 | Idempotency-Key | partial | Required on `/bookings/hold` + `/bookings/v2` only — not global |
| 25 | Webhook signature when secret set | done | Cashfree HMAC path in payments |
| 26 | Owner/admin gate on onboarding | done | Onboarding router owner/admin checks |
| 27 | Full IDOR pytest matrix + gitleaks + TOTP | not_started | Checklist unchecked |
| 28 | Slot inventory VR GAMING ADDA on live API | done | Checklist marked done (historical verify) |
| 29 | Sandbox ₹ payment with real Cashfree account | not_started | Checklist unchecked; Cashfree unset on live |

### B. Discovery module — steps 30–37

| # | Step | Status | Evidence |
|---|---|---|---|
| 30 | Phase 0 audit | done | `DISCOVERY_AUDIT.md` |
| 31 | Phase 1 schema / migration 023 | partial | In repo: `023_discovery_read_model.py`; live API still `774af3d` — migrate/deploy pending |
| 32 | Phase 2 Celery denorm (availability / rating) | partial | `tasks/discovery.py` + beat entries; Celery process not in Render blueprint |
| 33 | Phase 3 `GET /api/v1/discovery/centres` | done | `domains/discovery/router.py` + asyncpg `service.py` (mounted in `main.py`) |
| 34 | Phase 4 Redis geohash cache + ETag | done | `domains/discovery/cache.py` |
| 35 | Phase 5 Flutter discovery feature | done | `lib/features/discovery/` + route `/discover` |
| 36 | Phase 6 list UI / filters | done | `discovery_page.dart`, `filter_sheet.dart`, keyset cursor client |
| 37 | Phase 7 load / EXPLAIN / p95 gate | not_started | AGENT.md: “In progress” / needs Render after migrate; PR #6 left open |

### C. Availability & Booking Lock — steps 38–46

| # | Step | Status | Evidence |
|---|---|---|---|
| 38 | Phase 0 audit | done | `AVAILABILITY_AUDIT.md` |
| 39 | Phase 1 `tstzrange` / `during_*` + `booking_unit_locks` | partial | Migration `024` in repo; live deploy/migrate pending |
| 40 | Phase 2 EXCLUDE GiST (23P01) | partial | Constraints in `024` + `LockService`; effective only after migrate on PG |
| 41 | Phase 3 hold / release + Redis hint + rate limits | done | `POST /bookings/hold`, `/release` in `availability_router.py` |
| 42 | Phase 4 pay + guarded status + late-pay refund queue | done | `POST /bookings/{id}/pay` + `auto_refund` enqueue |
| 43 | Phase 5 WS + Redis Pub/Sub + snapshot `v` | done | `ws/router.py` `/api/v1/ws/clubs/{id}/availability`; `GET /clubs/{id}/availability` |
| 44 | Phase 6 Celery expire 30s / reconcile / refund | partial | Beat entries present; no Celery worker/beat in `render.yaml` |
| 45 | Phase 7 Flutter hold/pay/poll + `SlotGridController` | done | `gaming_booking_repository.dart` hold/release; `slot_grid_controller.dart` |
| 46 | Phase 8 PG concurrent acceptance test | partial | `tests/test_booking_lock_pg.py` exists; gated/skip without Postgres |

### D. Club Management — steps 47–52

| # | Step | Status | Evidence |
|---|---|---|---|
| 47 | Phase 0 discovery report | done | `CLUB_MGMT_DISCOVERY.md` (note: pre-022 classifications now stale) |
| 48 | Phase 1 data model + migration 022 | done | `022_club_management.py` + `club_ops/models.py` |
| 49 | Phase 2 APIs + Phase 2.5 rollups | done | `club_ops/router.py` (zones/resources/walk-in/live/customers/pricing/promos/revenue/occupancy); Celery rollup tasks in `celery_app.py`; `tests/test_club_ops.py` |
| 50 | Phase 3 Flutter owner UI | partial | `features/club_management/{data,domain}/` only — **no** `presentation/` screens |
| 51 | Phase 4 Angular admin oversight | partial | `club-management-list.component.ts` exists; not full override suite from build spec |
| 52 | Phase 5 tests (auth-bypass / Flutter / Angular) | partial | Backend `test_club_ops.py` present; Flutter/Angular club test coverage not complete per build spec |

---

## 8. Cross-cutting notes (requested)

### Money: float / Numeric vs paise

| Store | Type | Where |
|---|---|---|
| Integer paise (preferred for v2 / ledger / stations / club pricing) | `Integer` | `amount_paise`, `commission_paise`, `hourly_price_paise`, `payment_ledger.amount_paise`, `gaming_places.price_paise`, club pricing/promo fields |
| Legacy currency | `Numeric(10, 2)` | `gaming_bookings.price_per_hour` / `total_price` / `final_price` / …; `gaming_place_extensions.price_per_hour`; `gaming_slots.price_per_hour`; tournament `entry_fee` |
| Non-money floats | `Float` | lat/lng, ratings, media duration — not currency |

**Verdict:** **Mixed.** New paths use paise; legacy Numeric columns remain on the same booking rows.

### Shared enums

| Area | Fact |
|---|---|
| Users | SQLAlchemy/PG enum `user_role` (`UserRole`: user / parlor_owner / admin) |
| Club-ops | Python `Enum` + DB **CHECK** strings (`club_ops/enums.py`) — not PG ENUM types |
| Booking status | **String(20)** application strings — no shared DB enum / FSM table |
| Amenities | Bitmask helpers `app/core/amenities.py` + Flutter `lib/core/amenities.dart` |

### Soft delete

| Entity | Mechanism |
|---|---|
| Gaming places (extension) | `is_deleted` + `deleted_at` (+ `is_active`) — migration `020` |
| Reels / reel comments | `is_deleted` |
| Comments (posts) | soft-delete pattern in comment domain |
| Bookings | status → `cancelled` / `expired` (no `deleted_at` on `gaming_bookings`) |

### RBAC scoping

| Layer | Fact |
|---|---|
| Admin API | `_require_admin` → `UserRole.ADMIN` (`domains/admin/router.py`) |
| Club-ops | `ClubScope.resolve_club_id` — owner-scoped queries (`club_ops/router.py`) |
| Angular | `auth.guard` + `role.guard` |
| Gap | Admin Angular historically also had mock microservice; main API `/admin/*` is role-gated |

### Idempotency-Key coverage

| Endpoint | Required? |
|---|---|
| `POST /bookings/hold` | **Yes** (header) |
| `POST /bookings/v2` | **Yes** (header); unique `gaming_bookings.idempotency_key` |
| Cashfree webhooks | `webhook_events.event_id` unique + ledger `cf_event_id` |
| Legacy `POST` gaming booking / walk-in / tournament book | **No** Idempotency-Key |

### Pagination: cursor vs OFFSET

| Surface | Style |
|---|---|
| Discovery `GET /discovery/centres` | **Keyset cursor** (`next_cursor` / `encode_cursor`) |
| Comments / some reel comments | `after_id` cursor-ish |
| Admin lists, bookings lists, posts/reels feeds, DMS, geo search | **`OFFSET` / page** (dominant pattern elsewhere) |

---

## 9. Key file index

| Area | Path |
|---|---|
| Tables / models | `backend/app/domains/gaming_place/models.py`, `gaming_booking/models.py`, `gaming_booking/inventory_models.py`, `club_ops/models.py`, `user/models.py`, `tournament/models.py` |
| Migrations | `023_discovery_read_model.py`, `024_booking_lock_ranges.py`, `022_club_management.py`, `021_cashfree_slots_onboarding.py` |
| Lock / hold | `gaming_booking/lock_service.py`, `availability_router.py`, `availability_service.py` |
| Discovery | `domains/discovery/{router,service,cache,db}.py`, `tasks/discovery.py` |
| Club ops | `domains/club_ops/{router,service,enums}.py` |
| Payments | `domains/payments/{router,cashfree_client}.py` |
| WS | `app/ws/{router,events,manager}.py` |
| Runtime | `render.yaml`, `backend/scripts/render-start.sh`, `backend/Dockerfile`, `docker-compose.yml` |
| Flutter | `frontend/gamer_circle/pubspec.yaml`, `lib/features/{booking,discovery,club_management}/` |
| Angular | `admin-microservice-complete/frontend/package.json`, `src/app/` |
| Prior audits | `DISCOVERY_AUDIT.md`, `AVAILABILITY_AUDIT.md`, `CLUB_MGMT_DISCOVERY.md` |

---

## 10. Phase-0 stop / ops blockers (facts)

1. **Live deploy lag:** API `git_sha=774af3d` lacks discovery + booking-lock commits on HEAD (`474c9a1`).
2. **Migrations 023 + 024** must run on Render Postgres before PostGIS discovery path / EXCLUDE locks are live.
3. **Celery worker + beat** are not declared in `render.yaml` / `docker-compose.yml`.
4. **TOCTOU remains** on legacy create, walk-in, and tournament booking paths.
5. **Money dual-write:** paise + Numeric coexist on `gaming_bookings`.

**Step 1 (this audit) complete. No schema/API/UI code changed.**
