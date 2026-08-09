# AVAILABILITY_AUDIT — Live Availability & Booking Lock (Phase 0)

**Scope:** existing booking / hold / payment / realtime surface.  
**Rule:** change nothing in this phase — facts only.  
**Date:** 2026-08-09  
**Repo commit base:** `main` @ discovery merge (`ddd72d6`).

> Spec uses `resources` and `bookings`. This audit substitutes the **real** table names below.

---

## Spec term → real name

| Spec term | Real table / concept | Notes |
|---|---|---|
| club / parlor | `gaming_places` | Canonical venue (not legacy `parlors`) |
| resource (bookable unit) | `club_resources` | Per-PC / console / seat; optional on customer bookings |
| resource (capacity bucket) | `parlor_stations` | Aggregate count per `station_type` (PC, PS5, …) |
| booking | `gaming_bookings` | Primary customer booking row |
| hold | `booking_holds` + `gaming_bookings.hold_expires_at` | Hold is a side-effect of online create, not a dedicated API |
| slot grid row | `gaming_slots` | Materialized hourly rows (`slot_date` + `start_time`/`end_time`) |
| payment ledger | `payment_ledger` | Cashfree money movements |
| webhook idempotency | `webhook_events` | Unique `event_id` |
| tournament booking | `bookings` | **Separate** product — out of parlor time-grid scope |

---

## 1. Canonical schema (what exists today)

### 1.1 `gaming_bookings` (source of booking truth for parlors)

Key columns (migrations `010`, `021`, `022`):

| Column | Type / notes |
|---|---|
| `id`, `booking_ref` | UUID PK; unique human ref |
| `user_id`, `parlour_id` | FKs → `users`, `gaming_places` |
| `slot_id` | FK → `gaming_slots` |
| `resource_id` | Optional FK → `club_resources` (club-ops / walk-in; **not** set on customer v2 create) |
| `slot_date`, `start_time`, `end_time` | **date + time columns — not `tstzrange`** |
| `duration_hours`, `units`, `station_type` | v2 inventory fields |
| `booking_status`, `payment_status` | `String(20)` — **no DB CHECK / enum** |
| `hold_expires_at` | UTC expiry for online holds |
| `idempotency_key` | Partial unique (v2 create) |
| `cf_order_id`, `payment_session_id`, `payment_id` | Cashfree / payment refs |
| `amount_paise`, `commission_paise` | Money |

**No `EXCLUDE` / GiST / time-range constraint** on this table (or on `booking_holds`).

### 1.2 `booking_holds`

| Column | Notes |
|---|---|
| `booking_id` | Unique FK → `gaming_bookings` |
| `parlor_id`, `station_type`, `date`, `start_time` | Capacity key |
| `duration_hours`, `units` | Occupancy weight |
| `expires_at` | Authoritative TTL in app logic |
| `released` | Bool — released holds ignored by availability |

### 1.3 `parlor_stations` vs `club_resources`

- **`parlor_stations`:** capacity model used by customer availability (`total_count` per type).  
- **`club_resources`:** labeled physical units (PC-01, …) with `status` CHECK (`available|occupied|reserved|maintenance|offline`).  
- Customer v2 path books **station_type + units**, not a specific `club_resources` row → dual inventory models coexist.

### 1.4 `gaming_slots`

Hourly materialized inventory with `max_players` / `current_bookings` counter.  
A **second** inventory truth alongside bookings+holds. Discovery `available_now` denorm reads slots, not holds.

---

## 2. Booking status values & transition guards

### Observed `booking_status` strings (application-level only)

| Status | How it appears |
|---|---|
| `confirmed` | Legacy create; pay-at-parlor; payment success; owner confirm |
| `payment_pending` | v2 online create |
| `initiated` | Referenced in expire/availability filters — **never assigned** on create paths found |
| `expired` | `AvailabilityService.expire_hold` |
| `refund_pending` | Late payment after expire in `confirm_payment` |
| `cancelled` | User / owner / admin cancel |
| `checked_in` / `completed` / `no_show` | Club-ops lifecycle (`club_ops/enums.py`) |

`payment_status` in use: `pending`, `paid` (admin aggregations also tolerate aliases).

### Is there a real state machine?

**No.** No Python enum FSM, no DB CHECK on `booking_status`, no documented legal-transition table.

### Guarded `UPDATE … WHERE status = :expected`?

**Not found** anywhere under `backend/`.  
Pattern in use: `SELECT … FOR UPDATE` → Python `if` → mutate ORM object → `commit`.

Relevant code:

- `expire_hold` — rejects unless status ∈ `{payment_pending, initiated}` then sets `expired`  
  (`availability_service.py`)
- `confirm_payment` — idempotent if already `confirmed`+`paid`; if `expired` → `refund_pending` (does **not** auto-call Cashfree refund); else → `confirmed`/`paid`
- Club-ops soft guards in Python (`cannot check in cancelled/…`); no CAS SQL

---

## 3. Overlap / double-booking protection — **critical finding**

| Mechanism | Present? | Detail |
|---|---|---|
| Postgres `EXCLUDE USING gist (resource_id WITH =, during WITH &&)` | **No** | Zero `tstzrange` / `EXCLUDE` on bookings |
| Unique constraint on time window | **No** | Uniques are refs / idempotency / `cf_order_id` |
| App-level capacity check then insert | **Yes** | v2: `compute_availability` → validate → `INSERT` |
| `SELECT FOR UPDATE` | **Partial** | Station row + `GamingSlot` on v2; slot on legacy |
| Redis `SET NX` as correctness | **Legacy only** | `lock:gaming_slot:{id}` (5s) on legacy create; **not** on v2 |
| Hold TTL | **Yes** | `HOLD_MINUTES = 7`; Celery countdown + 5‑min sweep |

### TOCTOU — live double-booking race (flag for Phase 2)

Customer v2 create (`AvailabilityService.create_booking_v2`):

1. `SELECT parlor_stations … FOR UPDATE` (skipped if **no** station row — synthetic default has nothing to lock)
2. `compute_availability` — unlocked `SELECT` of bookings + holds, Python overlap math
3. `INSERT gaming_bookings` (+ optional `booking_holds`)
4. Increment `gaming_slots.current_bookings`

**Between steps 2 and 3 another transaction can commit.** That is exactly the SELECT-then-INSERT race the spec forbids. Redis is not in this path. Postgres does not refuse the second insert.

Legacy path (`GamingBookingService.create_booking`) uses Redis NX **and** `FOR UPDATE` on the slot, then bumps a counter — still **not** an exclusion constraint; Redis blip / multi-unit multi-hour windows remain application-fragile.

### Additional correctness gaps

1. **Double-count while held:** `payment_pending` bookings **and** their `BookingHold` rows both add to `used` in `compute_availability` → capacity looks lower than reality during a hold.
2. **`checked_in` invisible to customer grid:** occupying set is `confirmed|payment_pending|initiated` only; club-ops `OCCUPYING_STATUSES` includes `checked_in`.
3. **Per-resource walk-ins** use app-level busy-id sets (`club_ops`) — no DB exclusion for `resource_id` overlaps.
4. **Two inventory truths:** `gaming_slots.current_bookings` vs bookings/holds counts can diverge if expire/cancel paths miss a counter update.

---

## 4. Payment webhook — idempotency

### Cashfree (primary for gaming v2)

| Piece | Location |
|---|---|
| HTTP | `POST /api/v1/payments/webhooks/cashfree` (`payments/router.py`) |
| Alias `/api/v1/webhooks/cashfree` | Mentioned in `main.py` comment — **not mounted** |
| Worker | Celery `booking.process_cashfree_webhook`; inline fallback if enqueue fails |

**Idempotency — mostly yes:**

1. Insert `webhook_events` with unique `event_id`; duplicate → early `{"duplicate":"true"}`
2. Celery skips if `processed`
3. `confirm_payment` short-circuits if already confirmed+paid
4. `payment_ledger.cf_event_id` partial unique
5. Booking create requires `Idempotency-Key` → unique `idempotency_key`

**Gaps vs Phase 4 spec:**

- Late success after expire → status `refund_pending` only; **no** automatic `auto_refund` provider call in this path
- Failure / unpaid webhook types: no dedicated fail→release handler found (expiry sweep is the release path)
- Event id fallback uses `event_time` / random UUID if provider omits id — weak uniqueness if payload shape drifts
- Inline fallback and Celery path can both try confirm; rely on `confirm_payment` idempotency + row locks

### Razorpay

Legacy/tournament verify endpoints exist; **no** Razorpay webhook table for gaming holds. Legacy `POST /bookings/{id}/pay` still ties to Razorpay stub in places.

---

## 5. Uvicorn workers (decides Phase 5 Pub/Sub)

| Source | Behavior |
|---|---|
| `render.yaml` default start | Single `uvicorn` process, **no `--workers`** |
| `USE_FULL_BOOT=1` → `scripts/render-start.sh` | `uvicorn … --workers "${WEB_CONCURRENCY:-1}"` |
| `.env.example` | `WEB_CONCURRENCY=1` |
| `docker-compose.yml` | Backend only; **no Celery worker/beat service** |

**Conclusion for Phase 5:** production blueprint today is **1 worker**, so in-process socket fan-out would appear to work. Raising `WEB_CONCURRENCY` **without** Redis Pub/Sub fan-out would silently split viewers across workers. Phase 5 must still design Pub/Sub as if multi-worker is possible (and it is, via env).

### Existing realtime

- `WS /ws` + Redis channels `ws:{channel}` for messaging / notifications / friends / **tournament** `slot_booked`
- **No** parlor availability channel, no `slot_held` / `slot_released` / `slot_confirmed` deltas, no per-club version `v`

### Celery booking jobs (code present)

| Beat | Task | Schedule |
|---|---|---|
| `sweep-expired-booking-holds` | `booking.sweep_expired_holds` | every **5 min** (spec wants ~30s) |
| `nightly-booking-reconciliation` | `booking.nightly_reconciliation` | 02:15 IST |
| per-create countdown | `expire_booking_hold` | `HOLD_MINUTES * 60` |

**Infra gap:** Render/compose blueprints do **not** declare a Celery worker or beat process. Tasks exist in code; whether they run in prod depends on infra outside these files. Spec Phase 6 also wants `expires=` on every periodic task (only discovery beat currently sets that pattern consistently).

---

## 6. Existing API surface (vs hold/lock spec)

### Present

| Method | Path | Role |
|---|---|---|
| GET | `/api/v1/parlors/{id}/availability` | Hourly capacity grid (snapshot) |
| GET | `/api/v1/parlors/{id}/station-types` | Station catalog |
| POST | `/api/v1/bookings/v2` | Create + optional hold + Cashfree session (`Idempotency-Key` required) |
| GET | `/api/v1/bookings/{id}/status` | Poll; may confirm via Cashfree get_order |
| POST | `/api/v1/payments/webhooks/cashfree` | Provider webhook |
| POST | `/api/v1/bookings/{id}/pay` | Legacy Razorpay-oriented pay |
| POST | `/api/v1/bookings/{id}/cancel` | Cancel |
| Club-ops | `/api/v1/club/...` | Walk-in, check-in, live board, resource CRUD |

### Missing vs this spec

| Spec endpoint / behavior | Status |
|---|---|
| `POST /bookings/hold` | **Absent** (hold embedded in `/bookings/v2`) |
| `POST /bookings/{id}/release` | **Absent** (wait for TTL / expire job) |
| `POST /bookings/{id}/pay` → Cashfree + extend hold + guarded status | Partial / legacy; not Phase-4 shape |
| `WS …/clubs/{id}/availability` + deltas + `v` | **Absent** |
| `GET /clubs/{id}/availability?date=` with version | Closest: parlor availability without `v` |
| Rate limit: max 3 active holds / 10 attempts/min | **Absent** |
| Redis compare-and-delete Lua unlock | **Absent** on v2 |
| Hold TTL 8 min (spec) | Code uses **7** minutes |

### Flutter

`lib/features/booking/` talks to v2 availability + create + status poll.  
No dedicated hold/release client; no availability WebSocket; no per-cell slot state machine as specified in Phase 7.

---

## 7. Verdict for later phases (ordered)

1. **Phase 2 is mandatory and currently missing.** Without a Postgres `EXCLUDE` (or equivalent) on the live booking range, double booking is possible under concurrency. Redis must not be treated as the lock.
2. **Phase 1** must introduce `tstzrange` (or equivalent) on the booking/hold row that the exclusion indexes — today’s `slot_date`+`start_time`+`end_time` cannot host `&&` cleanly.
3. **Phase 3** should split hold from final booking create; today hold is inseparable from `/bookings/v2`.
4. **Phase 4** has a partial late-pay path (`refund_pending`) but no automatic refund / no CAS `WHERE status=`.
5. **Phase 5** has reusable Redis WS plumbing, but **zero** availability fan-out; design for multi-worker even though default is 1.
6. **Phase 6** must tighten expire cadence (30s vs 5min), add reconcile/auto_refund, and ensure worker/beat actually run in prod.
7. **Phase 7–8** acceptance tests (100 concurrent holds → exactly 1) will fail on current code — that is the Phase 2 gate.

---

## Key file index

| Area | Path |
|---|---|
| Models | `backend/app/domains/gaming_booking/models.py`, `inventory_models.py`, `club_ops/models.py` |
| Migrations | `010_add_gaming_booking_tables.py`, `021_cashfree_slots_onboarding.py`, `022_club_management.py` |
| Availability / hold | `backend/app/domains/gaming_booking/availability_service.py`, `availability_router.py` |
| Legacy booking + Redis lock | `backend/app/domains/gaming_booking/service.py` |
| Payments webhook | `backend/app/domains/payments/router.py`, `tasks/booking_tasks.py` |
| Celery beat | `backend/app/tasks/celery_app.py` |
| Runtime | `render.yaml`, `backend/scripts/render-start.sh`, `backend/Dockerfile` |
| WebSocket | `backend/app/ws/router.py`, `backend/app/ws/events.py` |
| Flutter | `frontend/gamer_circle/lib/features/booking/` |

---

**Phase 0 complete. Stop here — do not start schema/constraint work until this audit is accepted.**

---

## Implementation status (Phases 1–7 landed on `cursor/availability-booking-lock-46ce`)

| Phase | Status |
|---|---|
| 1 Schema `tstzrange` / `during_*` + `booking_unit_locks` | Done — migration `024_booking_lock_ranges` |
| 2 EXCLUDE GiST (SQLSTATE 23P01) | Done — `excl_booking_unit_locks_overlap` (+ resource exclude) |
| 3 Hold / release + Redis hint + rate limits | Done — `POST /bookings/hold`, `/release` |
| 4 Pay + guarded status + late-pay refund queue | Done — `POST /bookings/{id}/pay`, `auto_refund` |
| 5 WS + Redis Pub/Sub deltas + snapshot `v` | Done — `/api/v1/ws/clubs/{id}/availability`, `GET /clubs/{id}/availability` |
| 6 Celery expire 30s / reconcile / refund | Done — beat entries with `expires=` |
| 7 Flutter hold/pay/poll + `SlotGridController` | Done — repository + grid controller |
| 8 PG concurrent acceptance test | Gated — `test_booking_lock_pg.py` (skip without Postgres) |

**Ops required:** `alembic upgrade head` on Render (024), ensure Celery worker + beat run.
