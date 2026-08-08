# AGENT.md — GameConnect / ParLour

> Read this file FIRST, every session, before touching any code.
> This file IS your memory. Grok Code has no memory between sessions — this replaces that.

---

## 1. AGENT OPERATING ASSUMPTION (how to treat me — read this before calibrating tone)

**Operate as if working alongside a senior, cross-stack engineer. No hand-holding, no over-explaining fundamentals, no hedging. Give direct, production-grade output by default.** Where I'm still genuinely building depth (flagged below), give the senior-level answer first, then a one-line note on the non-obvious part — not a tutorial.

### Skill domains this agent should assume for me
- **Frontend / UI:** Angular (standalone components, `inject()`, signals) — production depth, 6 years. Also capable across general UI/UX implementation — component design, responsive layout, accessibility basics.
- **App development:** Flutter + Riverpod (`AsyncNotifier`) — actively building this depth through this exact project. Treat as "strong working proficiency, still sharpening," not beginner.
- **Backend:** Python/FastAPI, plus Java/Spring Boot (learned by mapping to Angular mental models — controller≈component, service≈service, repository≈HTTP client layer).
- **Database:** PostgreSQL — joins, indexes, window functions, `EXPLAIN ANALYZE`, PostGIS geo queries. DBeaver as primary GUI.
- **DevOps/Cloud:** AWS (S3, RDS at minimum — via this project's DMS/presigned URL and Postgres-on-RDS setup), CI/CD concepts, containerization. Assume working familiarity; go deep only where a project decision genuinely needs it.

### Where to still explain (don't skip these)
- Flutter/Riverpod idioms and FastAPI-specific patterns not yet codified in Section 6 — one-line Angular/Spring equivalent is enough, not a full lesson.
- Any AWS/DevOps service being used for the first time in this project — brief rationale, not a tutorial.

**Instruction to Grok Code:** Default to senior-level, terse, direct output across all domains above. Only slow down for the two "still explain" cases — and even then, one line of context, not a walkthrough. Never re-ask about experience level; this section is the answer.

---

## 2. WHAT I'M TRYING TO ACHIEVE

- Ship a working full-stack social + booking platform (GameConnect/ParLour) end-to-end: Flutter mobile app, FastAPI backend, Postgres/PostGIS database, Angular admin panel — all wired together, not just isolated feature demos.
- Use this project as the vehicle to become genuinely production-capable in FastAPI and Flutter (not just copy-pasting Grok's output — understanding it).
- Every feature should be usable end-to-end: if a user-facing feature ships, the admin panel must be able to see/manage/moderate it. No orphaned features that exist on mobile but are invisible to admin, or vice versa.
- Keep token/session cost low — this file exists so I don't re-explain context every session.

---

## 3. ARCHITECTURE — ALL LAYERS

| Layer | Tech | Role |
|---|---|---|
| Mobile app | Flutter, Riverpod (`AsyncNotifier` for state) | End-user app: booking, messaging, social feed |
| Admin panel | Angular (standalone components, `inject()`) | RBAC-gated internal tool: manage users, bookings, content moderation, reporting |
| Backend API | Python FastAPI | Single source of truth for business logic, serves both Flutter app and Angular admin |
| Database | PostgreSQL + PostGIS | Core data + geo queries (slot/location search) |
| Cache/presence | Redis | Online status, session cache, rate limiting |
| Background jobs | Celery | Async tasks — notifications, image processing, scheduled jobs |
| Realtime | WebSocket pub/sub | Messaging, live booking status updates |
| File storage | S3 (presigned URLs via centralized DMS) | User uploads, media |

### Core feature areas
- OYO-style slot booking (with PostGIS-backed location/availability search)
- Snapchat-style ephemeral messaging
- Instagram-style social feed/flows
- Full RBAC admin panel (roles, permissions, moderation tools)

---

## 4. PROJECT STRUCTURE (lives in a separate file — read it, don't skip it)

**File/folder layout and how everything connects across layers is maintained in `STRUCTURE.md`, not here.** This section changes rarely; `STRUCTURE.md` changes almost every session. Keeping them separate means Grok never has to re-read this whole rules file just to look up which file talks to which — it reads the small, fast-changing one instead.

**Instruction to Grok Code:** Before starting any task, read `STRUCTURE.md` and check its connectivity map (Section 2 of that file) for the relevant domain/trigger. Read only the listed files first — widen the search only if they don't contain what's needed. After finishing the task, follow `STRUCTURE.md` Section 4's update protocol (add/edit a row only if the file structure actually changed — most bug-fix tasks require no update at all).

## 5. CROSS-LAYER INTEGRATION RULE (important — this is what "everything integrated" means)

**Every change must be checked against this list before being considered "done":**

When you change/add... | ...you must also check/update:
---|---
A new DB column or table | FastAPI schema (Pydantic model) + migration file + any Angular admin table/form that lists that entity
A new FastAPI endpoint | Flutter API client method + Angular admin API service method (if admin needs visibility) + RBAC permission check if it's an admin-facing action
A new user-facing Flutter feature | Corresponding admin visibility: can an admin see/moderate/disable this? If not, flag it explicitly as "admin panel gap — deliberate or oversight?"
A new WebSocket event | Both Flutter listener AND any admin-side live view that should reflect it (e.g. live booking status)
A new S3/DMS upload type | Presigned URL generation logic on backend + cleanup/moderation path visible in admin
Any RBAC permission | Reflected in both the Angular route guards AND backend endpoint-level permission checks (never trust frontend-only gating)

**Instruction to Grok Code:** After implementing any feature, explicitly state which of the above integration points were touched and which were deliberately skipped (and why). Don't silently leave a layer out.

---

## 6. ESTABLISHED PATTERNS & CONVENTIONS (don't re-derive, don't re-suggest alternatives unless asked)

- **Flutter state:** Riverpod `AsyncNotifier` for all async state — not `StateNotifier`, not raw `FutureProvider` for anything with side effects.
- **Angular:** standalone components only, `inject()` for DI — no NgModules, no constructor injection.
- **Backend structure:** FastAPI routers per domain (booking, messaging, social, admin) — not one monolithic router file. (Current: domains/<domain>/router.py + service.py etc.)
- **Caching/presence:** Redis for online status and hot-path caching — not the DB for anything ephemeral.
- **Background work:** anything not needed in the immediate request/response cycle goes to Celery (notifications, image processing, scheduled cleanup).
- **Realtime:** WebSocket pub/sub pattern — messaging and live status updates, not polling.
- **File uploads:** always via S3 presigned URLs through the centralized DMS — never direct backend file handling.
- **Geo queries:** PostGIS functions (`ST_DWithin`, `ST_Distance`, geography type) with GIST indexes — never naive lat/lng range filtering.

---

## 7. CURRENT STATE (update this section every session — overwrite, don't append)

- **Last completed:** 2026-07-28 — Angular admin live on Render free static site: https://gamer-circle-admin.onrender.com (srv-d9kch1laeets73an3tc0, commit e23a4d3). API still https://gamer-circle-api.onrender.com healthy. Fixed parlor-onboarding TS prod build break.
- **In progress:** none
- **Next up:** Set CASHFREE_* for real UPI; Flutter Cashfree SDK; admin refund UI polish; concurrent capacity pytest; rotate Render API key
- **Known open issues / blockers:** Cashfree keys not set (mock_mode); Twilio optional; rotate Render API key still in .env

---

## 8. DECISIONS ALREADY MADE (don't re-litigate unless something changed)

- _(add entries here as you make firm architectural decisions, e.g. "chose WebSocket over polling for booking status — decided 2026-07-xx")_

---

## 9. CHANGELOG (append only — newest at top, keep each entry to 1-2 lines)

- 2026-07-28 — Deploy Angular admin free Static Site on Render (`gamer-circle-admin`); fixed onboarding TS build; render.yaml + SPA rewrite; API free web already live.
- 2026-07-28 — Spec stack: stations/hours/holds/ledger/webhooks + bookings/v2 + availability + Celery holds + Flutter station/duration/Book Now + Angular onboarding; live booking confirmed.
- 2026-07-28 — SlotEngine auto-generates gaming_slots on GET /parlors/{id}/slots; Cashfree create-order + webhook; Flutter date= query fixed.
- 2026-07-24 — Render LIVE: logs showed alembic 019_users_bio missing on old deploy + exit 255; redeployed sit 34501ec uvicorn-only; health/ready/DB/Redis OK.
- 2026-07-24 — API fail root: pure uvicorn boot (USE_FULL_BOOT=0), capped DB wait, SEED off; API_FAILURE_ANALYSIS.md.
- 2026-07-24 — Prod diag: E_* Flutter errors, /ready hints, API status banner, redeploy_production.sh, rebuild APK script, startCommand uvicorn fallback.
- 2026-07-24 — Fail-safe Render start (no set -e, always uvicorn), render_seed_boot.py, build import_ok check; redeploy push b58f67d.
- 2026-07-24 — Render Failed recovery: short Redis boot, JWT env fallback, 45s seed timeout, ALLOWED_HOSTS=*; GitHub Actions deploy-render + CI on sit.
- 2026-07-23 — Prod E2E: password login accepts phone; seed always ensures admin; Angular env → Render; mock fallback off in prod; prod_smoke_test.py + PRODUCTION_DEPLOYMENT.md.
- 2026-07-23 — Admin parity: full parlor CRUD/soft-delete/manager assign on main API; posts/reels/comments/likes/tournaments/ratings/stories moderation; Angular env → main backend; parlor create/edit form.
- 2026-07-18 — Production ready: render APP_ENV=prod, OTP bypass forced off in prod, /ready probe, Twilio errors hardened, Flutter prod flavor, no Dio logs/OTP hints in release, HTTPS network security, release APK → Render.
- 2026-07-18 — Render Blueprint (`render.yaml`: Postgres+Redis+API), DATABASE_URL asyncpg/SSL normalize, render-start.sh migrations+PostGIS; Flutter API_BASE_URL dart-define; Android AGP/Kotlin fix; release APK → Render URL; pushed `sit`.
- 2026-07-11 — Added + (create) button to lower navbar; then full check+fix pass until 0 errors: fixed ranked override name, dms_upload FilePicker via alias + pinned file_picker ^7 + integration_test sdk in pubspec, re-ran pub get + analyze x times (0 errors now).
- 2026-07-10 — Algorithm brain kit: migrations+models+full engine (track/compute/score/rank/build/trending/smart_search), Celery beat tasks, routers for ranked/interactions/search/admin, Flutter repo+providers+Trackable+home integration. Progress tracked in PROGRESS_ALGORITHM.md
- 2026-07-08 — Added PROFILE icon to lower navbar (6th position); implemented profile picture change (camera overlay on avatar, gallery upload via DMS, update avatar_url)
- 2026-07-08 — Full demo seed: 6 users (phones +91999999901X / Demo@123), 6 bookings, 6 posts (picsum), 5 reels (public mp4), convos/messages, gaming extensions for Delhi parlors
- 2026-07-08 — Placed AGENT.md + STRUCTURE.md (real paths + connectivity examples) into repo root per instructions
- _(session date)_ — _(what shipped)_

> Once this section exceeds ~15 entries, summarize the oldest 10 into one paragraph and move full detail to `AGENT_ARCHIVE.md`. Grok never reads the archive unless explicitly told to.

---

## 10. SESSION START — PASTE THIS AS YOUR FIRST MESSAGE

```
Read AGENT.md AND STRUCTURE.md in the repo root fully before doing anything else.
Do not re-explain the stack, architecture, or file layout back to me — just 
confirm in one line that both are loaded, then wait for my task.
Use STRUCTURE.md's connectivity map to jump straight to relevant files instead 
of scanning the repo. Apply the cross-layer integration rule (AGENT.md Section 5) 
to anything you build this session without me having to ask.
```

## 11. SESSION END — DO THIS BEFORE CLOSING

Ask Grok Code to output, in this exact format, at the end of every session:

```
Give me a session summary in this format only:
LAST COMPLETED: <1 line>
IN PROGRESS: <1 line>
NEXT UP: <1 line>
BLOCKERS: <1 line, or "none">
CHANGELOG ENTRY: <1 line, dated>
STRUCTURE.md UPDATE NEEDED (per its own update protocol, section 4 of that file): <diff-style note, or "none">
```

Paste LAST COMPLETED / IN PROGRESS / NEXT UP / BLOCKERS into Section 7 (overwrite), the CHANGELOG ENTRY into Section 9 (append, newest on top), and the STRUCTURE.md update (if any) directly into `STRUCTURE.md` per its own update protocol — don't let Grok rewrite that whole file, just apply the diff it gives you.
