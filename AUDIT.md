# AUDIT.md — Master Build Plan Step 1 (Stage 0)

**Scope:** map existing codebase. **No application/schema changes.**  
**Date:** 2026-08-09  
**Repo HEAD:** `sit` @ `474c9a1` (discovery PR #6 + booking-lock PR #8).  
**Live API:** `https://gamer-circle-api.onrender.com` `/ready` last observed `git_sha=774af3d` (ancestor — **pre-023/024** until redeploy + migrate).

> Spec uses `clubs` / `resources` / `bookings`. **Substitute these real names everywhere after this file.**

---

## 1. Spec term → real table names (canonical substitution)

| Spec term | **Real name — use this** | Notes |
|---|---|---|
| clubs / centres | **`gaming_places`** | Canonical venue catalog |
| club overlay (owner, soft-delete, ₹) | **`gaming_place_extensions`** | `owner_id`, `is_deleted`, `price_per_hour` |
| zones | **`club_zones`** | Migration `022` |
| resources (physical unit) | **`club_resources`** | PC-01, console, seat… |
| resources (capacity bucket) | **`parlor_stations`** | `total_count` per `station_type` |
| bookings | **`gaming_bookings`** | Primary parlor booking |
| holds | **`booking_holds`** + `hold_expires_at` | Side table + column |
| lock / EXCLUDE rows | **`booking_unit_locks`** | Correctness layer (024) |
| slots (hourly materialization) | **`gaming_slots`** | Legacy counter inventory |
| reviews | **`parlour_ratings`** | |
| users | **`users`** | Roles: `user` / `parlor_owner` / `admin` |
| ledger | **`payment_ledger`** | Paise entries |
| webhooks | **`webhook_events`** | Unique `event_id` |
| tournament bookings | **`bookings`** | **Separate** product — out of parlor EXCLUDE |
| legacy venues | **`parlors`** | Old PostGIS table; not discovery source |

**Key columns on `gaming_bookings`:**  
`booking_ref`, `user_id`, `parlour_id`, `resource_id`, `slot_date`/`start_time`/`end_time`, `during_start`/`during_end` (+ PG `during tstzrange`), `booking_status`/`payment_status` (strings), `amount_paise`/`commission_paise`, `idempotency_key`, `hold_expires_at`, `station_type`/`units`/`duration_hours`, **plus legacy `Numeric(10,2)` money columns**.

---

## 2. Extensions — postgis / btree_gist / pg_trgm

| Extension | Can be installed? | Evidence |
|---|---|---|
| **postgis** | Yes | Migrations `005`, `023`; `render-start.sh`; compose image `postgis/postgis:16-3.4-alpine` |
| **pg_trgm** | Yes | Migration `023` `CREATE EXTENSION IF NOT EXISTS pg_trgm` |
| **btree_gist** | Yes | Migration `024` (needed for scalar `=` inside GiST `EXCLUDE`) |

**Ops:** extensions are created by Alembic / start script on the **external** Render Postgres — not by the API Docker image. Live DB may not have run `023`/`024` yet (`git_sha` lag).

---

## 3. Booking overlap — is SELECT-then-INSERT still live?

| Path | Status | Detail |
|---|---|---|
| Hold / `/bookings/v2` (online) | **Fixed in repo** | Insert `booking_unit_locks` → catch `23P01`. Migration `024` EXCLUDE. `lock_service.py` |
| Availability **read** grid | SELECT-only (OK) | `compute_availability` for UI — not the write path |
| **Legacy** `POST /bookings` | **Still TOCTOU** | Redis NX + `FOR UPDATE` on `gaming_slots` counter — **no** unit locks |
| **Walk-in** `club_ops.create_walk_in` | **Still TOCTOU** | App picks free resource → plain INSERT — **no** EXCLUDE |
| **Tournament** `bookings` | Separate | Redis + `FOR UPDATE`; different table |

**Verdict:** Step 8 is **partial**. Customer hold path is correct in code; walk-in + legacy create still double-bookable under concurrency. EXCLUDE is inert until `alembic upgrade` applies `024` on Render.

---

## 4. Flutter state management

| Item | Fact |
|---|---|
| Library | **`flutter_riverpod` ^2.5.1** + `riverpod_annotation` |
| Also | `go_router`, `dio`, freezed |
| **Not used** | Bloc, GetX, Provider (package) |

**Keep Riverpod only.** Do not add a second state library (Master Plan Step 35).

---

## 5. Angular admin

| Item | Fact |
|---|---|
| Path | `admin-microservice-complete/frontend/` |
| Version | **Angular 21.2.x** (`@angular/core` lock **21.2.17**) |
| Architecture | **Standalone only** (`bootstrapApplication`, `standalone: true`) — **0 NgModules** under `src/` |

---

## 6. Uvicorn workers (decides Step 15 / 21 WS fan-out)

| Source | Value |
|---|---|
| `render.yaml` | `WEB_CONCURRENCY=1`; default start = single uvicorn (no `--workers`) |
| `render-start.sh` | `--workers "${WEB_CONCURRENCY:-1}"` when full boot |

**Today: 1 worker.** Raising concurrency without Redis Pub/Sub would split WS viewers. Availability WS already publishes on Redis (`avail:{club_id}` / `ws:*`) — Step 15 is largely in place for multi-worker.

**Celery worker/beat:** coded in `celery_app.py` — **not** declared as Render/compose services. Periodic expire/reconcile/discovery may not run in prod.

---

## 7. Status of Master Plan Steps 1–52

Legend: **done** · **partial** · **not_started** · **n/a** (this audit step)

| Step | Priority | Status | Evidence / gap |
|---|---|---|---|
| **1** Map codebase → AUDIT.md | 🔴 | **done** | This file |
| **2** Single enum source `shared/enums.yaml` → py/dart/ts + CI | 🔴 | **not_started** | Scattered Python enums / string statuses; no yaml codegen |
| **3** Money = integer paise everywhere | 🔴 | **partial** | Paise on ledger/stations/v2/`amount_paise`; legacy `Numeric(10,2)` still on `gaming_bookings` / slots / offers; Angular has currency pipe but not paise-lint |
| **4** Soft delete + public short codes + audit table | 🔴 | **partial** | `is_deleted` on extensions/comments; not universal on bookings/resources/users; `booking_audit` exists; no `PYT-…` short codes |
| **5** RBAC `require(*perms)` + club scope | 🔴 | **partial** | Club-ops scopes by `gaming_place_extensions.owner_id` → 403 cross-club (`test_club_ops`); no staff/admin sub-roles ops/finance/support; no generic `require(*perms)` |
| **6** API conventions (Idempotency, cursor, ORJSON, GZip) | 🟡 | **partial** | `/api/v1/*`, error `{code,message,details}`, GZip + orjson on discovery; Idempotency-Key only on hold/v2; **OFFSET** still common outside discovery |
| **7** Schema zones + resources + `tstzrange` | 🔴 | **partial** | Zones/resources `022`; `during` tstzrange `024`; legacy date+time columns remain |
| **8** EXCLUDE constraint; delete SELECT-then-INSERT writes | 🔴 | **partial** | EXCLUDE on `booking_unit_locks`; hold/v2 use it; **walk-in + legacy create still TOCTOU** |
| **9** Concurrency test 100 holds ×20 → exactly 1 | 🔴 | **partial** | `tests/test_booking_lock_pg.py` exists; **skipped without Postgres**; not proven on Render |
| **10** Hold endpoint TTL 8m, Lua unlock, rate limits | 🔴 | **done** (repo) | `POST /bookings/hold`, `HOLD_MINUTES=8`, Lua release, 3 holds / 10 attempts/min |
| **11** State machine + CHECK on status | 🔴 | **partial** | Guards via `UPDATE WHERE status`; statuses `held`/`payment_pending`/…; **no DB CHECK** enum |
| **12** Payment webhook = source of truth | 🔴 | **partial** | Cashfree webhook + `webhook_events` idempotency; client poll exists as backup |
| **13** Post-expiry payment → refund, no overwrite | 🔴 | **done** (repo) | `refund_pending` + `auto_refund` task |
| **14** Celery expiry 30s + reconcile + expires= | 🔴 | **partial** | Tasks + beat config present; **no Celery process in Render blueprint** |
| **15** WS + Redis Pub/Sub deltas + snapshot `v` | 🟡 | **done** (repo) | `WS /api/v1/ws/clubs/{id}/availability`; `GET /clubs/{id}/availability?date=` + `v` |
| **16** Owner onboarding wizard (map pin, save per step) | 🟡 | **partial** | Owner station/hours/closures APIs + Angular parlor onboarding; not full PENDING_REVIEW wizard with map-pin-only address |
| **17** Bulk device creation | 🟡 | **not_started** | No “Add 10 → PC-01…PC-10” API/UI |
| **18** Structured specs + global games catalogue | 🟡 | **partial** | `specs` jsonb on stations/resources; no global games tick-list |
| **19** Device status model (system vs owner) + maintenance force-choice | 🟡 | **partial** | `club_resources.status` CHECK; no cancel/reassign forced flow on maintenance |
| **20** `price_rules` table | 🟡 | **partial** | `club_pricing_rules` exists (day/hour slabs) — close; not exact `hour_range` + zone/resource matrix as specified |
| **21** Geo schema + indexes (discovery) | 🔴 | **done** (repo) | `023` PostGIS + partial indexes; bbox fallback if no PostGIS |
| **22** Celery precompute availability/ratings/search_doc | 🔴 | **done** (repo) | `discovery.refresh_*` + search_doc trigger in `023` |
| **23** One discovery query/endpoint | 🔴 | **done** (repo) | `GET /discovery/centres` asyncpg + keyset cursor |
| **24** Redis discovery cache + ETag | 🟡 | **done** (repo) | geohash key, TTL, stampede NX, ETag |
| **25** Map clustering | 🟢 | **not_started** | No `/discovery/clusters` |
| **26** Auth phone OTP + rate limits + JWT/refresh | 🟡 | **partial** | Auth module + JWT; Twilio OTP paths; rate limits / DLT / refresh-family revoke need audit depth |
| **27** Flutter auth UX (SMS Retriever, secure storage, Dio mutex) | 🟡 | **partial** | Dio + secure storage patterns exist; full SMS Retriever + single-flight refresh not verified complete |
| **28** Age gate (DOB server-side) | 🟡 | **not_started** | No DOB/age policy flow |
| **29** Location permission deferred + city picker | 🟡 | **partial** | Discovery page exists; permission UX not fully as specified |
| **30** Referral | 🟢 | **not_started** | |
| **31** Centre page one aggregate endpoint | 🟡 | **partial** | Parlor detail endpoints exist; not single `/clubs/{id}?lat&lng` aggregate as specified |
| **32** Booking flow 3 screens (time before device) | 🟡 | **partial** | Booking feature exists; not reordered 3-screen flow |
| **33** Checkout rules (poll webhook, countdown expires_at) | 🟡 | **partial** | `pollUntilTerminal` + hold/pay in repo; UI not fully wired |
| **34** Offline-verifiable QR | 🟡 | **not_started** | |
| **35** Flutter hygiene (one state lib, dark mode, …) | 🟢 | **partial** | Riverpod + go_router already; dark mode / error map incomplete |
| **36** Owner live device grid landing | 🟡 | **partial** | `/club/live` API; Flutter owner grid UI incomplete |
| **37** QR check-in | 🟡 | **partial** | Check-in APIs in club-ops; offline HMAC QR not built |
| **38** Walk-in via same bookings + EXCLUDE | 🔴 | **partial** | Walk-in → `gaming_bookings` `is_walk_in=True` ✅; **does not use EXCLUDE/LockService** ❌ |
| **39** Cancel / reschedule (atomic reschedule) | 🟡 | **partial** | Cancel exists; reschedule-as-one-txn not present |
| **40** Append-only ledger | 🔴 | **partial** | `payment_ledger` append-style; not full immutable ledger + compensating entries product |
| **41** Revenue display (4 lines + CSV) | 🟡 | **partial** | Club revenue/occupancy APIs; not full owner finance UI |
| **42** Settlement / Cashfree payout | 🟡 | **not_started** | |
| **43** Staff role + offline outbox | 🟡 | **not_started** | No staff role table; owner-only scope |
| **44** Admin auth + TOTP + maker-checker | 🔴 | **not_started** | Admin JWT/role only; no TOTP / pending_approvals CHECK |
| **45** Approval queue (KYC) | 🟡 | **not_started** | |
| **46** Admin dashboard six metrics | 🟡 | **partial** | Angular analytics/dashboard components; not metrics_daily-backed six KPIs |
| **47** Commission freeze at confirm | 🟡 | **partial** | `commission_paise` on booking; no global/override rate admin product |
| **48** Three-way reconciliation UI | 🟡 | **partial** | `reconciliation_issues` + nightly task; no exception UI |
| **49** Refunds via gateway state machine | 🟡 | **partial** | `auto_refund` / refund_pending; not full requested→approved→… UI |
| **50** User 360 / fraud / reports | 🟢 | **not_started** | |
| **51** Tournaments via same booking lock | 🟢 | **partial** | Tournament domain exists; **separate** `bookings` table — can double-sell venue |
| **52** Full acceptance gate | 🔴 | **not_started** | Unit/PG-gated tests only; no load/EXPLAIN/WS/QR matrix run |

---

## 8. Cross-cutting gaps (feed Stage 1)

| Topic | Fact |
|---|---|
| Shared enums | **No** `shared/enums.yaml` |
| Float money | **Yes** — `Numeric(10,2)` on legacy booking/slot/offer paths |
| Soft delete universal | **No** — extensions/comments yes; bookings/resources/users incomplete |
| Idempotency-Key | **hold + v2 only** |
| Pagination | Discovery = **cursor**; most other lists = **OFFSET** |
| ORJSON + GZip | Discovery path yes; not universal default response class |
| Public short codes `PYT-…` | **No** |
| Staff / admin sub-roles | **No** |

---

## 9. Three launch decisions (from plan — unresolved)

1. **Commission on cash walk-ins** — not decided in code (walk-ins write `gaming_bookings`; commission behavior unclear).  
2. **Under-18 booking policy** — no DOB/age gate.  
3. **Tournament entry fees** — legal; free-entry not enforced as v1 policy.

---

## 10. Recommended next step

**Step 2 🔴 — Single enum source** (`shared/enums.yaml` → Python / Dart / TypeScript + CI ban on hand-edits).

Do **not** start Step 2 until this audit is accepted.

**Blocking correctness still open after recent work:**  
apply **023+024** on Render · wire walk-in/legacy through EXCLUDE · run Step 9 on Postgres · run Celery in prod · finish Step 2–6 foundations.

---

**⛔ Stage 0 Step 1 complete. Stop here.**
