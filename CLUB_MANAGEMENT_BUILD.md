# Paythan — Club Management System (Owner Operations) — Agent Build Spec

**How to use this file:** This is a build order for a coding agent (Claude Code / Grok Code),
not a wishlist. Run it **one PHASE at a time**, each in a fresh session, `/clear` between phases.
Do NOT paste the whole file and say "build it all." That fails every time.

Recommended per phase: `claude --strict-mcp-config --mcp-config ./.mcp.json`, Sonnet for
Phases 1–4, Opus only if Phase 0 or a migration gets hairy.

---

## GLOBAL RULES (apply to every phase — the agent must obey these)

1. **Discover before you write.** Read the actual code. Never assume a path, model name,
   service boundary, or convention — grep for it and confirm.
2. **Reuse, do not recreate.** This project already has: a slot engine, booking flow,
   owner dashboard, admin revenue panel, Cashfree payments, auth/JWT, and the Flutter theme
   files (`app_colors.dart`, `app_text_styles.dart`, `app_spacing.dart`, `app_theme.dart`).
   If a capability exists, extend it. If you are about to create a second Booking model,
   STOP — you have misunderstood the codebase.
3. **No new UI primitives.** Owner screens must be built from existing widgets/components and
   the existing theme tokens. Match the current layout, spacing, and typography exactly. If a
   needed component does not exist, add it to the shared component layer, not inline.
4. **Migrations are reversible and non-destructive.** Never drop or rename an existing column
   without an explicit go-ahead from the human. Additive migrations only unless told otherwise.
   Every migration has a working `downgrade`.
5. **Multi-tenant scoping is mandatory.** Every new query, endpoint, and screen is scoped to the
   owner's club(s). An owner must never see another club's seats, bookings, customers, or revenue.
   Enforce at the query layer, not just the UI.
6. **Money is stored as integer paise.** No floats for currency, anywhere. Display formats to ₹.
7. **Timezone is Asia/Kolkata** for all business logic (peak hours, day-of-week, daily rollups).
8. **`data-testid` via `Semantics`** on every new interactive Flutter widget (existing testing
   requirement). Angular gets `data-testid` attributes.
9. **One phase = one PR.** Update `PROGRESS.md` at the end of each phase. Do not start the next
   phase's work.

---

## ASSUMPTIONS (I made these because you said "assume everything it needs" — correct any that are wrong)

- **Owner-facing UI = Flutter** (mobile + web). **Platform-admin oversight = Angular admin.**
  So the Club Management System's primary surface is the Flutter owner app; the Angular admin gets
  read-only oversight + override controls, not the full owner workflow.
- Backend is **FastAPI microservices + PostgreSQL + Celery/Redis**. Club-ops logic lives in the
  service that already owns partners/clubs (agent confirms the exact service in Phase 0).
- Migration tool is **Alembic** (agent confirms in Phase 0).
- A "resource" is the generic unit: **seat, PC, console, PS5, pool table, VR rig.** One model,
  typed — not seven models.
- Heavy analytics are **precomputed by Celery into rollup tables**, not calculated on request.
- Pricing and promotions **feed the slot engine's price computation** — they do not fork it.

---

## PHASE 0 — DISCOVERY & GAP ANALYSIS  (NO CODE. Output a report only.)

Produce `CLUB_MGMT_DISCOVERY.md` answering all of the below. Do not write any feature code
in this phase. When done, stop and wait for review.

**Backend**
- List the microservices and which one owns clubs/partners, bookings, and payments.
- Find the existing Booking model, Slot/SlotEngine, and the Cashfree integration point. Paste the
  file paths and the model/class signatures.
- Where is auth/JWT enforced? How is the current owner identified from a request? How is club
  ownership represented (owner_id on club? a membership table?)?
- What migration tool + how are migrations run? Paste one existing migration as a style reference.
- Is there already anything resembling: seats/resources, pricing rules, promotions, occupancy?
  For each of the 7 features, classify as: **EXISTS / PARTIAL / MISSING** with the file path.

**Flutter**
- Paste the contents of the 4 theme files and 2–3 existing owner screens so the new screens copy
  the exact patterns (state management, folder structure, API client, routing).
- How does the owner app currently talk to the backend (dio? repository pattern? which folder)?
- Confirm how `Semantics`/`data-testid` is currently applied.

**Angular admin**
- Paste the module/routing structure and one existing feature module (component + service + model)
  as the pattern to copy. Confirm the API service and auth interceptor pattern.

**Deliverable:** the classification table (7 features × EXISTS/PARTIAL/MISSING), a short
"what I will reuse vs build" plan, and any place where my assumptions above were wrong.

> Everything after this point is contingent on Phase 0. If Phase 0 shows a feature already
> exists, the corresponding work below shrinks to "extend," not "build."

---

## PHASE 1 — DATA MODEL + MIGRATIONS  (backend only)

Add only what Phase 0 marked MISSING/PARTIAL. Reuse existing Booking/User/Club/Payment models.

Proposed new entities (adjust names to existing conventions):

- **Resource** — belongs to a club. Fields: `type` (enum: seat|pc|console|ps5|pool|vr|other),
  `name/label`, `zone_id` (FK), `status` (available|occupied|reserved|maintenance|offline),
  `specs` (JSONB, for PCs), `hourly_rate_override` (paise, nullable), `layout_x`/`layout_y`
  (for floor map), `is_active`.
- **Zone** — belongs to a club. `name`, `sort_order`. Groups resources ("PS5 Zone", "PC Arena").
- **PricingRule** — belongs to a club. `applies_to` (resource_type | resource_id | zone_id),
  `base_rate` (paise/hour), `time_slabs` (JSONB: peak/off-peak windows + multiplier or flat),
  `day_of_week_overrides` (JSONB), `package_defs` (JSONB: e.g. 3hr bundle price), priority.
- **Promotion** — belongs to a club. `type` (percent|flat|happy_hour|first_visit|loyalty|code),
  `value`, `code` (nullable, unique per club), `valid_from`/`valid_to`, `usage_limit`,
  `used_count`, `applicable_resource_types` (JSONB), `is_active`.
- **ClubCustomer** — links a User to a Club (do NOT duplicate User). `visit_count`, `total_spend`
  (paise), `last_visit_at`, `loyalty_points`, `tags` (JSONB), `notes` (text), `is_banned`.
- **OccupancyRollup** — precomputed. `club_id`, `resource_id`/`zone_id`, `bucket_start`
  (hour granularity), `occupied_minutes`, `booking_count`, `no_show_count`, `revenue` (paise).
  Written by Celery, read by analytics endpoints.

Add FKs, indexes on (`club_id`, common filter cols), and the enum types. Write upgrade +
downgrade. Update the ER section of `STRUCTURE.md`. **Stop after migrations run clean on a
scratch DB. Do not write endpoints yet.**

---

## PHASE 2 — BACKEND SERVICES + APIs  (feature by feature)

All endpoints club-scoped from the JWT owner identity. Follow the existing router/service/schema
layout found in Phase 0. Suggested surface (rename to match conventions):

**Seat/PC Management**
- CRUD `Zone`, CRUD `Resource`, `PATCH /resources/{id}/status` (single + bulk),
  `PUT /clubs/{id}/floor-layout` (save x/y positions).

**Booking Management (owner side — EXTEND existing booking, do not fork)**
- `GET /owner/bookings?date=&view=day|week` (calendar), `POST /bookings/{id}/confirm|cancel`
  (cancel needs reason), `POST /bookings/walk-in` (create without customer app),
  `POST /bookings/{id}/check-in|check-out|extend|no-show`.
- `GET /owner/live` — who is playing right now, driven by check-in/out.

**Customer Management**
- `GET /owner/customers?search=`, `GET /owner/customers/{id}` (with visit history from Booking),
  `POST /owner/customers/{id}/note`, `POST .../tag`, `POST .../ban`.
- On check-out, update `ClubCustomer` aggregates (visit_count, total_spend, last_visit).

**Pricing Control**
- CRUD `PricingRule`, `POST /pricing/preview` (given resource + start + duration → computed
  price, showing which rule/slab applied). **The slot engine must call this resolver** so the
  booking price and the preview never diverge. Refactor the engine to use one price resolver.

**Promotions & Offers**
- CRUD `Promotion`, `POST /promotions/validate` (code + booking context → valid? discount?),
  and hook application into the booking price computation before Cashfree charge.

**Revenue Dashboard (aggregate existing payment/commission data)**
- `GET /owner/revenue/summary?range=today|week|month` → gross, net after commission (from the
  monetization spec), by resource type, by payment method, booking count, avg session value.

**Occupancy Analytics (read rollups only)**
- `GET /owner/occupancy/timeseries`, `.../heatmap` (hour × day-of-week), `.../utilization`
  (per resource/zone ranking), `.../no-show-rate`.

Write pytest coverage for pricing resolution, promo validation, and club-scoping (a cross-club
access attempt must 403). **Stop. Do not touch Flutter yet.**

---

## PHASE 2.5 — CELERY ROLLUP JOB

One periodic task that fills `OccupancyRollup` from Booking + check-in/out data (hourly buckets),
plus a backfill command for historical data. Idempotent (safe to re-run a bucket). Register in the
existing Celery beat schedule. This is what makes Phase 4 analytics fast.

---

## PHASE 3 — FLUTTER OWNER UI  (reuse theme + existing screen patterns)

Build only after Phase 2 APIs are green. Every screen uses the 4 theme files and the existing
API-client/state pattern from Phase 0. `Semantics` `data-testid` on all interactive widgets.
Match existing layout — no new visual language.

Screens (as a bottom nav / drawer section "Club Management"):
1. **Floor / Seats** — visual grid or floor map of resources, color-coded by status, tap to
   change status, long-press for detail. Reuse existing card/tile styles.
2. **Bookings** — day/week calendar, walk-in button, check-in/out, cancel-with-reason sheet.
3. **Live Now** — current occupants, time remaining, extend/checkout.
4. **Customers** — searchable list, detail with visit history, notes/tags, ban toggle.
5. **Revenue** — summary cards + chart, range toggle. Reuse whatever chart lib the app already uses.
6. **Pricing** — rules list + editor (base rate, peak/off-peak slabs, packages), price preview.
7. **Promotions** — list + editor (type, value, code, validity, limits), active/expired.
8. **Analytics** — occupancy heatmap, utilization ranking, no-show rate.

Wire loading/empty/error states using the app's existing convention. **Stop. Angular next.**

---

## PHASE 4 — ANGULAR ADMIN (platform oversight, not owner workflow)

Follow the existing module pattern from Phase 0. A "Club Management" section giving platform admins:
- Read-only view of any club's resources, live occupancy, revenue, occupancy analytics.
- Override controls: force-cancel a booking, disable a promotion, deactivate a resource,
  flag/ban a customer at platform level.
- All behind the existing admin auth guard/interceptor. Reuse existing table/card/chart components.

---

## PHASE 5 — TESTS (fold into existing TESTING_PLAN.md)

- Backend: pricing resolver, promo validation, rollup idempotency, and **club-scoping/auth-bypass**
  (cross-club access → 403) — this maps to the auth-bypass category already in TESTING_PLAN.md.
- Flutter: Playwright/widget tests keyed off the `data-testid`s added in Phase 3 for the booking
  and walk-in flows.
- Angular: component + service specs for the admin oversight views.

---

## DEFINITION OF DONE (per phase, before moving on)

- Migrations run clean up AND down on a scratch DB (Phase 1).
- New tests pass; a cross-club request is rejected (Phase 2/5).
- Rollup job runs and backfills without duplicating buckets (Phase 2.5).
- Owner screens match existing theme/layout; every interactive widget has a `data-testid` (Phase 3).
- `PROGRESS.md` updated; no work started for the next phase.

---

## THE FIRST MESSAGE TO SEND THE AGENT

> Read this file: CLUB_MANAGEMENT_BUILD.md. Execute **PHASE 0 only** — discovery and gap
> analysis, no code. Produce CLUB_MGMT_DISCOVERY.md with the 7-feature EXISTS/PARTIAL/MISSING
> table and the file paths I asked for. Then stop and wait. Do not start Phase 1.
