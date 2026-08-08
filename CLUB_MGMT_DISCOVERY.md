# CLUB_MGMT_DISCOVERY.md — Phase 0 Discovery & Gap Analysis

> Produced per `CLUB_MANAGEMENT_BUILD.md` Phase 0. No feature code was written. This is a
> read-only report. **Do not start Phase 1 until this is reviewed.**

---

## 0. Headline corrections to the spec's ASSUMPTIONS section

| Assumption in spec | Reality | Impact |
|---|---|---|
| "Backend is FastAPI **microservices**" | **Single FastAPI monolith.** One `backend/app` with 30 domain folders under `app/domains/`, one deploy unit, one Celery worker set. There *is* a separate `admin-microservice-complete/` directory with its own FastAPI backend, but it is a **disconnected, fully-mocked scaffold** (SQLite + `mock_store.py`) that the real Angular admin does **not** call — confirmed via `environment.ts`: the admin frontend hits the main backend's `/api/v1/admin/*` directly. Treat `admin-microservice-complete/backend` as noise; ignore it for Phase 1/2. | Simplifies Phase 1/2 — one codebase, one Alembic history, one place to add routers. |
| "Club-ops logic lives in the service that owns partners/clubs" | There is no "Club" entity. The real venue-ownership table is **`GamingPlaceExtension`** (an overlay on the synced `GamingPlace` catalog row), inside `app/domains/gaming_place/`. A separate `app/domains/parlor/` is a thin **facade** over the same table (owner-facing endpoints only — it explicitly refuses to create a second venue). A third, unrelated legacy `Parlor` ORM model (`app/domains/parlor/models.py`, own `parlors` table) is dead code, still imported in `app/db/models.py:40` but unused by the active service/repository. | New club-ops models (Resource, Zone, PricingRule, Promotion, ClubCustomer, OccupancyRollup) should FK to `gaming_places.id` (or `gaming_place_extensions.gaming_place_id`), **not** to the legacy `parlors` table. |
| "An owner's club(s)" (plural) | Ownership today is **one owner → at most one club**, enforced in code (`ParlorService.create_parlor` rejects a second parlor per owner; `ParlorRepository.get_by_owner_id` does `.limit(1)`). No staff/co-owner/membership table exists at all. | Multi-tenant scoping (Global Rule 5) is currently simpler (1:1) than the spec assumes, but if multi-club-per-owner is a real future requirement, that's a separate, larger change — flag explicitly rather than silently building for a plural that doesn't exist yet. |
| "A resource is the generic unit... one model, typed" | Closest existing thing is **`ParlorStation`** (`app/domains/gaming_booking/inventory_models.py`) — one row per `(parlor_id, station_type)` holding an **aggregate `total_count`**, not individual seat/unit identity. There is no per-unit row, no per-unit status, no `layout_x/layout_y`. | Confirms Resource/Zone are genuinely new work (see table below), but the new `Resource` model should probably *replace* `ParlorStation`'s role for capacity-counting once it exists, not sit beside it forever — flag as a Phase 1/2 design decision, not silently fork. |
| "Pricing and promotions feed the slot engine's price computation — they do not fork it" | **There are already two parallel booking/pricing code paths writing to the same `gaming_bookings` table**: (a) the older `GamingSlot`/`SlotEngine`/`GamingBookingService` flow, and (b) a newer `ParlorStation`/`BookingHold`/`AvailabilityService.create_booking_v2` flow with its own flat 10% commission calc. Neither has peak/off-peak pricing. Both compute price independently. | A pricing resolver (Phase 2) MUST be called from **both** paths, or it will diverge exactly the way Global Rule/spec worries about "booking price and preview never diverge." This is a bigger refactor than "extend the slot engine" — it's "unify two engines behind one resolver." Surface this to the human before Phase 2 starts. |
| "Heavy analytics are precomputed by Celery into rollup tables" | Confirmed **not yet true**. `AdminService.analytics()` computes everything live via on-request SQL aggregation. No rollup table exists anywhere. | Matches the spec's Phase 2.5 plan — no correction needed, just confirming MISSING. |
| Flutter: "Reuse whatever chart lib the app already uses" (Revenue/Analytics screens) | **No charting library exists in `pubspec.yaml` at all** — no fl_chart, no syncfusion, nothing. The existing "Owner Dashboard" renders stats as plain `Card`/`Text` tiles and a `ListTile` list. | Phase 3 Revenue/Analytics screens will need a **new dependency** added to `pubspec.yaml` — this is a deliberate, visible exception to Global Rule 2/3 ("reuse, no new primitives"), not an oversight, and should be called out to the human before Phase 3. |

---

## 1. BACKEND

### 1.1 Ownership / structure
- Single FastAPI app, `backend/app/main.py` (`FastAPI(title="GamerCircle API")`), ~30 routers mounted in one process. One `docker-compose.yml` (postgres + redis + backend). Celery workers/beat run from the same codebase (`app/tasks/celery_app.py`).
- Domain folders (`backend/app/domains/`): `admin, auth, booking, chat, comment, common, dms, feed, follow, friend, gaming_booking, gaming_place, geo, home, like, messaging, notification, online, parlor, payments, post, reel, search, snap_map, story, tournament, upload, user`.
- Venue/club ownership: `gaming_place` domain (`GamingPlace` + `GamingPlaceExtension`, latter has `owner_id`). `parlor` domain is a facade over it for owner-facing endpoints (`/parlors/me/analytics`, create/update/posts/tournaments). Bookings/slots/inventory: `gaming_booking` domain. Payments: `payments` domain (Cashfree + legacy Razorpay). Platform admin: `admin` domain.

### 1.2 Booking model + Slot/SlotEngine

`backend/app/domains/gaming_booking/models.py`:
```python
class GamingSlot(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "gaming_slots"
    parlour_id, parlour_game_id, slot_date, start_time, end_time,
    price_per_hour: Numeric(10,2), original_price: Numeric(10,2),
    max_players: int, current_bookings: int, is_available: bool

class GamingBooking(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "gaming_bookings"
    booking_ref, user_id (FK users), parlour_id (FK gaming_places),
    slot_id (FK gaming_slots), offer_id (FK parlour_offers),
    guest_name, num_players, slot_date, start_time, end_time,
    hours_booked, price_per_hour, total_price, tax_amount, discount_amount,
    final_price, payment_mode, payment_status, payment_id, booking_status,
    cancellation_reason/detail, cancelled_at, refund_amount, refund_status,
    free_cancellation_before, is_non_refundable, gc_points_earned,
    contact_email, contact_phone, gstin,
    # migration 021 additions:
    station_type, duration_hours, units, amount_paise, commission_paise,
    cf_order_id, payment_session_id, idempotency_key, hold_expires_at,
    updated_at, created_at
```
Also in this domain: `ParlourOffer`, `CancellationReason`, `ParlourRating`, `UserSearchHistory`, and (newer schema) `app/domains/gaming_booking/inventory_models.py`: `ParlorStation`, `ParlorHours`, `ParlorClosure`, `BookingHold`, `PaymentLedger` (entry_type: payment/refund/commission), `WebhookEvent`, `BookingAudit`, `ReconciliationIssue`.

SlotEngine — `backend/app/domains/gaming_booking/slot_engine.py`:
```python
class SlotEngine:
    def __init__(self, session: AsyncSession) -> None: ...
    async def ensure_slots_for_date(self, parlour_id: UUID, slot_date: date, *,
        open_time: time = DEFAULT_OPEN, close_time: time = DEFAULT_CLOSE) -> list[GamingSlot]: ...
    async def ensure_range(self, parlour_id: UUID, *, days: int = 14) -> int: ...
```
Price = `_default_price_for_place()` → flat `hourly_price`/`price_per_hour`/`starting_price`/`min_price` off `GamingPlaceExtension`, else `Decimal("99.00")`. No peak/off-peak, no pricing-rule table.

**Parallel newer path** — `app/domains/gaming_booking/availability_service.py`, `class AvailabilityService`: `compute_availability()`, `create_booking_v2()`, `expire_hold()`, `confirm_payment()`. Also flat pricing: `price_paise = stations[0].hourly_price_paise * duration_hours * units`; commission = `(price_paise * COMMISSION_BPS) // 10000`, `COMMISSION_BPS = 1000` (10%).

### 1.3 Cashfree integration

`backend/app/domains/payments/cashfree_client.py` — module-level functions, not a class:
```python
def is_configured(settings=None) -> bool
def verify_webhook_signature(raw_body, timestamp, signature, secret) -> bool
async def create_order(*, order_id, amount_paise, customer_id, customer_phone, return_url, notify_url, settings=None) -> dict
async def get_order(order_id, settings=None) -> dict
```
Falls back to a mock order (`status: "mock"`) when Cashfree keys aren't set.

`backend/app/domains/payments/router.py` (prefix `/payments`):
- `POST /payments/cashfree/bookings/{booking_id}/order`
- `POST /payments/webhooks/cashfree` — verifies HMAC, dedupes on `WebhookEvent.event_id`, queues `booking_tasks.process_cashfree_webhook.delay(...)`, inline fallback via `AvailabilityService.confirm_payment` if Celery is down
- `GET /payments/cashfree/config`
- Legacy Razorpay endpoints still present, hit a *different, older* `app/domains/booking/service.py::BookingService`.

### 1.4 Auth / JWT / ownership check

`backend/app/core/security.py`: `create_access_token`, `create_refresh_token`, `decode_token`.
`backend/app/core/dependencies.py`:
```python
async def get_current_user(credentials: HTTPAuthorizationCredentials | None, db: DbSessionDep, settings: SettingsDep) -> UserResponse
CurrentUserDep = Annotated[UserResponse, Depends(get_current_user)]
async def get_optional_current_user(...) -> UserResponse | None
```
Bearer JWT, `HTTPBearer(auto_error=False)`, standard dependency used across all routers.

Club ownership check example — `backend/app/domains/parlor/repository.py`:
```python
async def is_owned_by(self, parlor_id: UUID, owner_id: UUID) -> bool:
    result = await self.session.execute(
        select(GamingPlaceExtension.owner_id).where(
            GamingPlaceExtension.gaming_place_id == parlor_id,
            GamingPlaceExtension.owner_id == owner_id,
        )
    )
    return result.scalar_one_or_none() is not None
```
**Existing scoping gap found** (relevant to Global Rule 5): `app/domains/gaming_booking/onboarding_router.py` uses `_require_owner_or_admin(user)` — a **role-only** check (`user.role in (ADMIN, PARLOR_OWNER)`) with no verification that the user owns *this specific* `parlor_id`. Any `PARLOR_OWNER` can currently PUT stations/hours/closures for **any** `parlor_id` through that router. This predates Club Management work but sits directly in the area Phase 2 (Seat/PC Management) will extend — should be fixed alongside, not left as a silent pre-existing hole.

### 1.5 Migrations

Alembic confirmed (`backend/alembic/env.py`, async engine, 22 versioned files, `001`…`021_cashfree_slots_onboarding.py` + one autogenerate hash revision).

Style reference — `backend/alembic/versions/010_add_gaming_booking_tables.py` (full, both directions symmetric):
```python
def upgrade() -> None:
    op.create_table("gaming_slots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("parlour_id", sa.UUID(), nullable=False),
        sa.Column("slot_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("price_per_hour", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_available", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["parlour_id"], ["gaming_places.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gaming_slots_parlour_id_slot_date", "gaming_slots", ["parlour_id", "slot_date"])
    # ... gaming_bookings table with FKs to gaming_places/gaming_slots/users, indexes on user_id/parlour_id/booking_status

def downgrade() -> None:
    op.drop_index(...); op.drop_table("gaming_bookings")
    op.drop_index(...); op.drop_table("gaming_slots")
```
**Caution**: the newest migration (`021_cashfree_slots_onboarding.py`) uses raw `op.execute("ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...")` and its `downgrade()` does **not** reverse those column adds — an asymmetric downgrade. Global Rule 4 requires a working downgrade on every migration; **copy the style of `010`, not the downgrade-completeness of `021`.**

### 1.6 The 7-feature classification (matches Phase 2's 7 feature headers)

| # | Feature | Status | Evidence |
|---|---|---|---|
| 1 | **Seat/PC Management** (Resource/Zone) | **PARTIAL** | `ParlorStation` (`gaming_booking/inventory_models.py`) — aggregate `total_count` per `(parlor_id, station_type)`, no per-unit identity/status, no floor layout (`layout_x/y`), no `Zone` grouping concept at all. |
| 2 | **Booking Management** (owner side: calendar, walk-in, check-in/out, live) | **MISSING** (booking substrate itself EXISTS, owner-ops layer does not) | Zero matches anywhere in `app/` for `check_in`, `walk_in`, `no_show`. `booking_status` values in use: `confirmed`, `payment_pending`, `cancelled` — no `checked_in`/`no_show`. `ParlourRating.checkin_rating` is a cosmetic review sub-score, unrelated. No owner-facing bookings-calendar or walk-in-creation endpoint exists. |
| 3 | **Customer Management** (ClubCustomer CRM) | **MISSING** | Loyalty exists only as a *platform-wide* system: `GCPoints`/`GCPointsTransaction` (`gaming_booking/gc_points.py`) — not per-club, no visit_count/notes/tags/ban concept anywhere. |
| 4 | **Pricing Control** | **MISSING** (beyond flat rate) | Only flat `hourly_price_paise` (`ParlorStation`) / `price_per_hour` (`GamingPlaceExtension`/`GamingSlot`). No `PricingRule` model, no peak/off-peak, no day-of-week override, no package/bundle pricing, no shared resolver. (The only `peak_hour_start/end` hit in the codebase is unrelated — part of the trending/recommendation algorithm, `app/models/recommendation.py`.) |
| 5 | **Promotions & Offers** | **PARTIAL** | `ParlourOffer` + `OfferService` (`gaming_booking/offer_service.py`) — real percent/amount discount, min-hours, max-uses, validity window, `code` field. **But** wired only into the old slot-based flow; `AvailabilityService.create_booking_v2` (the newer path) hardcodes `discount_amount=Decimal("0")` — promos don't apply there. No generic cross-flow `Promotion` model. |
| 6 | **Revenue Dashboard** (owner-facing) | **MISSING** (platform-admin equivalent exists, owner-facing does not) | `AdminService.analytics()` (`admin/service.py`) computes revenue/bookings/growth live via SQL — but it's **platform-wide**, not club-scoped, and gross only (does not subtract `commission_paise`/`PaymentLedger` to get net). The owner-facing `/parlors/me/analytics` returns only `follower_count`/`total_posts`/`bookings_by_tournament` — no revenue figures at all. Building blocks (`commission_paise` column, `PaymentLedger` entries, the live-aggregation SQL pattern) exist and are reusable. |
| 7 | **Occupancy Analytics** | **MISSING** | No rollup table (`Occupancy`, `Rollup`, heatmap — zero matches). Nothing precomputed; nothing computed live either for occupancy specifically (only revenue/booking-count admin analytics exist). |

### 1.7 Celery

`backend/app/tasks/celery_app.py`:
```python
celery_app = Celery("paythan", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.beat_schedule = {
    "refresh-trending-1h": {...}, "refresh-trending-6h": {...}, "refresh-trending-24h": {...},
    "refresh-engagement-stats": {...}, "cleanup-old-data": {...},
    "sweep-expired-booking-holds": {"task": "booking.sweep_expired_holds", "schedule": crontab(minute="*/5")},
    "nightly-booking-reconciliation": {"task": "booking.nightly_reconciliation", "schedule": crontab(hour=2, minute=15)},
}
celery_app.conf.timezone = "Asia/Kolkata"
```
Task modules in `backend/app/tasks/`: `booking_tasks.py` (Cashfree webhook, hold sweep, reconciliation — natural home for a rollup task, or a new sibling `analytics_tasks.py`), plus `recommendation_tasks.py`, `media_tasks.py`, `story_cleanup.py`, `ephemeral_messages.py`, `push.py`, `background.py`.

### 1.8 Commission/revenue fields

`commission_paise` exists on `GamingBooking` (migration 021) and is computed as flat 10% (`COMMISSION_BPS = 1000`) inside `AvailabilityService.create_booking_v2` only — recorded to `PaymentLedger(entry_type="commission", ...)`. **Not** populated by the older slot-based flow, and **not** subtracted anywhere in `AdminService.analytics()`. A net-of-commission revenue dashboard needs new aggregation logic.

---

## 2. FLUTTER

### 2.1 Theme files (`lib/app/theme/`) — all 4 exist, confirmed and pasted in full during discovery
- `app_colors.dart` (95 lines) — brand/neutral-light/neutral-dark/semantic/domain-specific/legacy-alias/gradient/DM-palette color constants.
- `app_text_styles.dart` (78 lines) — display/headline/body/label `TextStyle` constants + a couple of color-applied convenience variants.
- `app_spacing.dart` (36 lines) — spacing scale (`xs..xxl`), radius scale, component sizing constants, screen padding.
- `app_theme.dart` (207 lines) — `AppTheme.light`/`AppTheme.dark` `ThemeData`, wires `AppColors`/`AppTextStyles` into `colorScheme`/button/input/card/divider themes. Convention: screens read via `Theme.of(context)`, not by re-importing `AppColors`/`AppTextStyles` directly (rare exceptions allowed).

### 2.2 Existing owner screens

Only two exist today (no "manage club" screens): `lib/features/parlor/presentation/owner_dashboard_screen.dart` and `parlor_profile_screen.dart`, reachable only via a `ListTile` in `settings_screen.dart` (**no drawer entry today** — an existing gap).

- `owner_dashboard_screen.dart` (99 lines) — stat-card row (`_StatCard` = `Card` + `Text` headline + label) + plain `ListTile` list for "bookings by tournament." **Bypasses the app's normal Riverpod convention**: calls `ref.read(socialApiProvider).fetchAnalytics()` directly in `initState`/`setState`, no `AsyncNotifier`. No `Semantics` usage.
- `parlor_profile_screen.dart` (137 lines) — card/tile + `TabBarView` (posts `GridView` / tournaments `ListView`) + follow/unfollow `FilledButton`. Same `ref.read(socialApiProvider)...` pattern, no dedicated notifier.
- `create_tournament_screen.dart` (96 lines) — closest existing form/editor pattern: `TextField`/`DropdownButtonFormField` list in a `ListView`, `FilledButton` submit with a `_submitting` bool guarding a `CircularProgressIndicator`.

**Important**: these three screens use the *older* legacy pattern (raw `ConsumerStatefulWidget`, no `AsyncNotifier`, loose `Map<String,dynamic>`). The **recommended** pattern — used by booking/search/tournament features — is `Notifier<CustomState>`/`AsyncNotifier` + typed repository. New Club Management screens should copy that, not `owner_dashboard_screen.dart`.

### 2.3 API client / repository / provider pattern (the one to copy)

`lib/core/network/dio_client.dart` (41 lines) — `Dio` with `baseUrl`, timeouts, JSON headers, conditional `LogInterceptor`, injected `AuthInterceptor`; registered in `get_it` DI, exposed via `dioProvider` in `lib/core/providers/dio_provider.dart`.

`lib/features/booking/data/gaming_booking_repository.dart` (177 lines) — canonical repository pattern: constructor-injected `Dio`, one method per endpoint, `try { ... } on DioException catch (e) { if (e.response?.statusCode == 404) return []; rethrow; }`, tolerant response parsing (`data is Map ? data['items']/data['slots'] : data as List`), typed return via `Model.fromJson`.

`lib/features/tournament/providers/tournament_provider.dart` (22 lines) — canonical `AsyncNotifier` example (`AsyncNotifierProviderFamily` + `FamilyAsyncNotifier`). For list/filter/pagination state (closer to what most Club Management screens need), the established pattern is a hand-rolled `Notifier<CustomState>` with an immutable state class + `copyWith` — see `lib/features/parlors/providers/parlor_search_provider.dart` and `lib/features/booking/providers/gaming_booking_provider.dart`.

### 2.4 Routing

`lib/app/router/app_router.dart` — `go_router`, `Provider<GoRouter>`. `/owner-dashboard` is a flat top-level `GoRoute` outside the `ShellRoute` (no bottom-nav chrome).

**No owner-role route guard exists** — only an authenticated-user guard, in `lib/app/router/router_notifier.dart::_isProtectedRoute`, which just string-matches route prefixes (`/owner-dashboard`, `/admin`, etc. are all just "requires login," never role-checked). A real Club Management section needing owner-only access will need this extended.

### 2.5 Semantics / testid convention

`Semantics(` appears in **exactly one file**, `lib/features/parlors/presentation/parlour_detail_screen.dart` (2 usages), with **no dedicated helper widget and no documented convention** anywhere in the codebase (`find` for `*testid*`/`*test_key*`/`keys.dart` — zero results):
```dart
Semantics(label: 'station_type_selector', child: Wrap(...));
Semantics(button: true, label: 'slot_${slot.startTime}', child: ChoiceChip(...));
```
`label:` is used ad hoc as a de facto testid (snake_case string); `button: true` added for tappable items. Flutter's `Semantics` widget has no `identifier:` param — Global Rule 8's "`data-testid` via `Semantics`" phrasing should be read as "use `label:` as the testid," matching this existing (thin) precedent, or a proper shared wrapper should be introduced in Phase 3 since none exists.

### 2.6 Chart library

**None.** `pubspec.yaml` has zero matches for `fl_chart`/`syncfusion`/`charts_flutter`/`graphic`. Confirmed via 0 matches and via the Owner Dashboard rendering stats as plain text tiles, not charts. Phase 3's Revenue/Analytics screens will need a new package added — flagged in Section 0 above as a deliberate exception to "no new primitives."

### 2.7 Navigation shell

`lib/features/shell/presentation/widgets/main_shell_scaffold.dart` — bottom nav is a hardcoded 3-tabs / center FAB / 3-tabs split (`for (var i = 0; i < 3; i++) ... for (var i = 3; i < 6; i++)`). **Adding a 7th tab will break this layout as a naive append** — needs an explicit split redesign (e.g. 3/4) if Club Management becomes a bottom-nav tab rather than a drawer entry.

`lib/features/shell/presentation/widgets/app_drawer.dart` — simpler `ListView` of `_DrawerTile`s in two groups (primary / secondary + Divider). A "Club Management" entry fits naturally in the secondary group here, consistent with (and finally fixing the absence of) an Owner Dashboard drawer entry.

---

## 3. ANGULAR ADMIN

### 3.1 Routing (`src/app/app.routes.ts`)

Flat, per-component **lazy loading via `loadComponent`** (no `NgModule`s, no `loadChildren` groupings) nested under one `AdminLayoutComponent` route guarded by `authGuard`. Existing feature routes: `dashboard, users, users/:id, parlors(+/new,/onboarding,/:id,/:id/edit), dms, posts(+/reels), social/likes, social/comments, tournaments, bookings, slots, offers, events, community, geo, ratings, analytics, roles(super_admin only), notifications, settings(super_admin only), unauthorized`. A "Club Management" section would add entries the same way, optionally `canActivate: [roleGuard('super_admin')]` for override-only screens.

### 3.2 Feature module pattern to copy — `src/app/features/parlors/`

Most complete existing CRUD feature: `parlors-list.component.ts` (710 lines, list+search+filter+`ngx-datatable`+row actions), `parlor-detail.component.ts` (671 lines, tabbed detail via `ngx-bootstrap` `TabsModule` + `StatsCardComponent`), `parlor-form.component.ts` (299 lines, `ReactiveFormsModule`, create/edit via route param detection). All templates are **inline** in the `.ts` file (no separate `.html`) — established convention. Standalone components, `ChangeDetectionStrategy.OnPush`, `inject()` everywhere, signals for state, `computed()` for permission-gated UI via `hasPermission(role, PERMISSIONS.X)`.

Models live in **one shared file**, `src/app/core/models/index.ts` — no per-feature model files. A `Club`/`ClubCreateRequest`/`ClubUpdateRequest` would be added there, following the existing `Parlor`/`ParlorCreateRequest`/`ParlorUpdateRequest` shape.

### 3.3 API service (`src/app/core/services/admin-api.service.ts`)

```typescript
@Injectable({ providedIn: 'root' })
export class AdminApiService {
  private readonly http = inject(HttpClient);
  private readonly mock = inject(MockDataService);
  private readonly base = `${environment.apiUrl}/admin`;
  private readonly allowMock = environment.useMockFallback === true;
  private mockOrThrow<T>(factory: () => T) { ... } // real call first, mock fallback only if allowMock
}
```
**Confirmed**: this points at the **real main backend** (`environment.apiUrl` = `http://localhost:8000/api/v1` dev, `https://gamer-circle-api.onrender.com/api/v1` prod) — not at `admin-microservice-complete/backend`. That separate backend is fully mock (SQLite + `mock_store.py`) and is not called by the running app at all; it's dead scaffold. Every new Club Management call goes through this same `AdminApiService`, hitting the main backend's `/api/v1/admin/*`.

### 3.4 Auth guard + interceptor

`core/guards/auth.guard.ts` (`auth.isAuthenticated() && auth.canAccessAdminPanel()`), `core/guards/role.guard.ts` (`roleGuard(requiredRole)` factory using `hasRole`), `core/interceptors/auth.interceptor.ts` (attaches `Authorization: Bearer`, handles 401 → refresh-and-retry → logout-on-failure). `core/constants/permissions.ts` defines `PERMISSIONS`/`hasPermission`/`hasRole` — a Club Management feature needs new constants there (`MANAGE_CLUBS`, etc.), same pattern as `MANAGE_PARLORS`.

### 3.5 Shared components (`src/app/shared/`)

`PageHeaderComponent` (title/subtitle/breadcrumbs + `<ng-content>` for actions), `StatsCardComponent` (KPI tile), `StatusBadgeComponent`, `EmptyStateComponent`, plus `date-format`/`currency-in`/`truncate` pipes. **No shared data-table wrapper** — every list screen embeds `ngx-datatable` directly; Club Management list screens should do the same.

### 3.6 `data-testid`

**Not used anywhere** in the admin frontend (`grep -rln "data-testid" src` → 0 matches). This is a fresh requirement to introduce in Phase 4, not an existing convention to extend.

---

## 4. WHAT I WILL REUSE vs. BUILD

**Reuse as-is:**
- Auth/JWT (`CurrentUserDep`), Cashfree client + webhook plumbing, Alembic setup, Celery app/beat registration point, `ParlourOffer`/`OfferService` (extend, don't replace, for promotions), `commission_paise`/`PaymentLedger` (extend for revenue net calc), Flutter theme files as-is, Flutter `DioClient`/repository/`Notifier` pattern, Flutter `Semantics(label:...)` convention, Angular routing/guard/`AdminApiService`/`PageHeaderComponent`/`StatsCardComponent`/permissions pattern.

**Extend, not fork:**
- `AvailabilityService`/`SlotEngine` → both must call one new pricing resolver (Phase 2 needs to explicitly unify these two paths, bigger than "refactor the engine").
- `ParlourOffer`/`OfferService` → wire into `create_booking_v2` (currently skipped there) instead of building a second promo mechanism.
- `_require_owner_or_admin` in `onboarding_router.py` → tighten to real per-club ownership check while Phase 2 touches this area anyway (pre-existing scoping gap).
- Owner Dashboard's drawer absence → fix by adding the new Club Management entry to `app_drawer.dart` (also finally surfaces Owner Dashboard itself).

**Genuinely new (nothing to extend):**
- `Resource`/`Zone` (real per-unit inventory + floor layout — `ParlorStation` is aggregate-only, doesn't cover this)
- `PricingRule` (peak/off-peak, day-of-week, packages — nothing exists beyond flat rate)
- `ClubCustomer` (per-club CRM — only platform-wide GCPoints loyalty exists)
- `OccupancyRollup` + Celery job (nothing precomputed exists)
- Owner-side booking lifecycle: check-in/out, walk-in, no-show, live-now (zero matches in codebase)
- Owner-facing revenue dashboard endpoint (platform-admin analytics exists but isn't club-scoped or net-of-commission)
- Flutter charting dependency (none exists — needs to be added, flagged to human)
- Flutter owner-role route guard (only auth guard exists today)
- Angular `data-testid` convention (introduced fresh)

## 5. Recommended sequencing note for the human

Two items above are bigger than the spec implies and are worth a decision before Phase 1/2 starts:
1. **Unifying the two booking/pricing paths** (old slot flow vs. `AvailabilityService` v2) behind one pricing resolver — this is real refactor risk, not additive.
2. **Multi-club-per-owner** is currently hard-blocked in code (`ParlorService.create_parlor`). If that's actually wanted eventually, it's out of scope for this spec but worth flagging now rather than discovering it mid-Phase-2.

**Stopping here per Phase 0 instructions — awaiting review before Phase 1.**
