# STRUCTURE.md — GameConnect / ParLour: File Map & Connectivity

> Purpose: answer "where does X live and what does it talk to" in one lookup, without scanning the repo.
> This file changes OFTEN (every session that adds/moves/connects a file). AGENT.md changes RARELY.
> Update rule: **append or edit only the specific row/line that changed — never regenerate this whole file.**

---

## 1. FOLDER TREE (update only when a folder is added/removed/renamed)

/backend
  /app/core/{config.py, dependencies.py, security.py, ...}
  /app/db/{base.py, models.py, session.py}
  /app/domains/<domain>/{router.py, service.py, schemas.py, models.py?, repository.py?}
  /app/domains/admin/router.py
  /app/domains/dms/{router.py, admin_router.py, service.py}
  /app/tasks/{celery_app.py, ...}
  /app/ws/{manager.py, router.py, events.py}
  /alembic/versions/*.py
  /scripts/{seed_*.py, run_dev.py}

/frontend/gamer_circle
  /lib/app/{app.dart, router/, di/, theme/, config/}
  /lib/core/{network/, providers/, services/, constants/, errors/, utils/, widgets/}
  /lib/features/<domain>/{data/, domain/, presentation/, providers/}
  /lib/shared/{models/, widgets/}
  /lib/main.dart

/admin-microservice-complete
  /frontend/src/app/{app.routes.ts, core/, features/<domain>/, layout/, shared/}
  /backend/app/{main.py, routers/, services/, schemas.py, models/}   # currently mock-heavy; main /admin/* now in backend/app/domains/admin
  /frontend/src/app/features/ has Angular standalone components

Note: Admin panel currently uses a separate microservice backend (mocks). Main backend provides real /admin/* routes under domains/admin + gaming_booking etc. Flutter app is primary client for core backend.
_(Update this block only on structural folder changes.)_

---

## 2. CONNECTIVITY MAP (the core of this file — update after every feature/change)

One row per **connected chain** — a single thread from UI to DB. Add a new row when a new chain is built. Edit only the affected row when a chain changes. Don't touch other rows.

| # | Trigger (UI/event) | Flutter file | → | FastAPI endpoint | → | Backend file(s) | → | DB table(s) | → | Admin file(s) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Load home / nearby parlors | `features/home/data/home_repository.dart` (via home_provider.dart) | → | `GET /api/v1/home` (and /nearby, /quick-picks) | → | `domains/home/router.py` → `domains/home/service.py` (uses GeoService, GamingBookingRepository, ParlorRepository, PostRepository) | → | `gaming_places`, `gaming_place_extensions`, `parlors`, `posts` | → | `admin-microservice-complete/frontend/src/app/features/parlors/parlors-list.component.ts` (via separate admin backend /admin; main backend /admin/stats etc not yet wired to this UI) |
| 2 | Gaming parlor slot booking | `features/booking/...` + parlour_detail slots tab; `gaming_booking_provider.dart` | → | `GET /parlors/{id}/slots?date=` (auto-materialize) · `POST /bookings` · `POST /payments/cashfree/bookings/{id}/order` | → | `slot_engine.py` + `parlor_router.py` + `service.py` + `payments/cashfree_client.py` | → | `gaming_slots`, `gaming_bookings`, `parlour_offers` | → | admin bookings list (main `/admin/*`); Cashfree webhook `/payments/webhooks/cashfree` |
| 10 | Discovery nearby list (distance/rating/available-now) | `features/discovery/presentation/discovery_page.dart` + `discovery_repository.dart` | → | `GET /api/v1/discovery/centres` | → | `domains/discovery/router.py` → asyncpg `service.py` + Redis `cache.py`; Celery `tasks/discovery.py` | → | `gaming_places` (read-model cols) | → | — (admin parlors list covers centres) |
| 3 | User auth (login/otp/signup) | `features/auth/{data/datasources/*, presentation/providers/*_notifier.dart}` | → | `POST /api/v1/auth/*` (otp, verify, login, signup, refresh) | → | `domains/auth/router.py` → `domains/auth/service.py` + providers/* + services/* | → | `users` | → | `admin-microservice-complete/frontend/src/app/features/users/users-list.component.ts` (via /admin/users on admin backend or main /admin/users) |
| 4 | Social feed / post like/comment | `features/feed/...` + `features/post/...` + `features/like/...` + `features/comment/...` + shared/post_card.dart | → | `GET/POST /api/v1/feed`, `/posts`, `/likes`, `/comments` | → | `domains/feed/router.py` + `domains/post/{router,service,repository}.py` + `domains/like/...` + `domains/comment/...` | → | `posts`, `reels`, `comments`, `likes`, `follows` | → | `admin-microservice-complete/frontend/src/app/features/posts/posts-list.component.ts`, `social/comments-list...`, `ratings/...` (some via mocks) |
| 5 | Reels (create/view) | `features/reels/{presentation/reels_screen.dart, create_reel_screen.dart, providers/reels_provider.dart}` + widgets | → | `GET/POST /api/v1/reels/*` | → | `domains/reel/router.py` → `domains/reel/service.py` + repository | → | `reels`, `reel_likes?` (see migrations) | → | `admin-microservice-complete/frontend/src/app/features/posts/reels-list.component.ts` |
| 6 | Messaging / DMs | `features/messaging/{data/messaging_repository.dart, presentation/chat_screen.dart, providers/messages_provider.dart}` | → | `GET/POST /api/v1/messaging/*` + WS | → | `domains/messaging/{router,service,repository,models}.py` + `domains/dms/*` + `app/ws/*` | → | `conversations`, `messages`, `media_assets` (via DMS) | → | `admin-microservice-complete/frontend/src/app/features/dms/dms-list.component.ts` (admin moderation) |
| 7 | Snap map / presence | `features/snap_map/{data/..., presentation/snap_map_screen.dart, providers/snap_map_provider.dart}` + online | → | `/api/v1/snap-map/*`, `/online/*` | → | `domains/snap_map/{router,service,models}.py` + `domains/online/{router,service,models}.py` + ws | → | `user_locations`, `online_status` | → | — (no admin visibility yet) |
| 8 | Admin stats / users (real) | — (Angular admin not yet pointed at main backend) | → | `GET /api/v1/admin/stats`, `/admin/users` etc | → | `domains/admin/router.py` (requires ADMIN role) + user models | → | `users`, `parlors`, `gaming_places` | → | `admin-microservice-complete/frontend/src/app/core/services/admin-api.service.ts` (currently hits mock admin micro) + features/users/ etc. |
| 9 | DMS upload (presigned) | `core/services/dms_service.dart` + `shared/widgets/dms_upload_widget.dart` | → | `POST /api/v1/dms/presign` etc | → | `domains/dms/router.py` → service.py + admin_router.py | → | `media_assets` | → | `admin-microservice-complete/frontend/src/app/features/dms/dms-list.component.ts` + posts media viewer |
| 10 | | | | | | | | | | |

**Column meaning:**
- **Trigger**: the human-readable action that kicks off this chain (helps you find it later without knowing file names).
- **Flutter file**: exact file with the widget/provider that starts the call.
- **FastAPI endpoint**: exact route + method (include /api/v1 prefix where applicable).
- **Backend file(s)**: router → service → (model if relevant), in call order. Use domains/ paths.
- **DB table(s)**: tables actually touched (from alembic models or explicit).
- **Admin file(s)**: the admin component/service that can see or manage this data, if any. Write `— (no admin visibility yet)` if none exists — don't leave it blank, so gaps are visible at a glance.

Note: Many admin Angular components currently fallback to mocks in admin-microservice-complete/backend. Real admin integration uses main backend /admin/* + role check. Cross-link as chains are wired.

---

## 3. SHARED/CROSS-CUTTING FILES (things many chains depend on — list once, reference by name above)

| File | Used by | Purpose |
|---|---|---|
| `backend/app/domains/dms/service.py` + router | any upload chain (reels, posts, messaging, profile) | S3 presigned URL generation + asset tracking |
| `backend/app/ws/manager.py` + router + events | messaging, live booking status, snap_map, online | WebSocket pub/sub hub + redis listener |
| `backend/app/core/dependencies.py` | all routers needing db/redis/user | FastAPI deps: DbSessionDep, RedisDep, CurrentUserDep |
| `frontend/gamer_circle/lib/core/network/dio_client.dart` + auth_interceptor | all Flutter API calls | Shared Dio instance + auth header injection |
| `frontend/gamer_circle/lib/app/di/injection.dart` + providers | Flutter Riverpod setup | DI wiring for repositories/providers |
| `backend/app/tasks/` (celery) | notifications, media, story cleanup, ephemeral | Background jobs |
| `backend/alembic/versions/` (esp recent like 016_*) | schema evolution | Migrations for all tables |
| `admin-microservice-complete/frontend/src/app/core/guards/` (auth.guard, role.guard) | Angular admin routes | RBAC |
| `backend/app/domains/common/` | cross domain (notifications, exceptions, otp, social_notify) | Shared domain logic |

---

## 4. UPDATE PROTOCOL (how Grok Code should maintain this file — cheaply)

**After finishing any task that touches files:**
1. Did this task create a **new connected chain** (new feature end-to-end)? → Add one new row to Section 2.
2. Did it **change a link in an existing chain** (e.g. swapped which service file handles it)? → Edit only that row's relevant cell.
3. Did it add a **new shared/cross-cutting file**? → Add one row to Section 3.
4. Did it add a **new top-level folder**? → Edit Section 1 only.
5. None of the above (bug fix within an existing file, styling tweak, etc.)? → **Don't touch this file at all.**

**Instruction to Grok Code:** Output updates as a diff-style note — "Section 2, add row: ...", "Section 2, row 3, Admin file column: ..." — not a full file rewrite. I will paste the exact change in myself. This keeps the update cheap and keeps me from having to review a full regenerated file every time.

---

## 5. HOW TO USE THIS FILE (for lookups, not just updates)

- Starting a task on an existing feature? Search Section 2 for the trigger/domain name first — gives you every file in that chain in one line, instead of asking Grok to explore the repo.
- Wondering if something has admin visibility yet? Scan the "Admin file(s)" column — any `— (no admin visibility yet)` is a known gap, already flagged, no need to re-derive it.
- Onboarding a new session cold? Read this file top to bottom once — it's short by design.
