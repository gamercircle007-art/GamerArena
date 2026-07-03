# ADMIN MICROSERVICE — GROK FIRST SESSION
# Paste this ENTIRE file when starting fresh OR after context loss.
# Then say: "Scan my project → read PROGRESS_ADMIN.md → build next unchecked task."
# ═══════════════════════════════════════════════════════════════════════════════

## WHAT THIS PROJECT IS
A **completely separate admin microservice** for GameConnect / ParLour platform.
- Runs independently from the main Flutter + FastAPI app
- Connects to the SAME PostgreSQL database
- Its own auth (admin_users table — not the app's users table)
- React + TypeScript frontend (NOT Flutter)
- FastAPI backend on port 8001 (main app is on port 8000)
- Accessible at: http://admin.parlour.in (or localhost:3001 in dev)

## THIS PROJECT IS SEPARATE FROM (don't mix with):
- backend/ (main FastAPI app — port 8000) ← different project
- frontend/parlour_app/ (Flutter app) ← different project
- admin-microservice/ (THIS project) ← what we are building here

## HOW THEY CONNECT
```
Main PostgreSQL DB ←── Main FastAPI (port 8000) ←── Flutter App
         ↑
Admin FastAPI (port 8001) ←── React Admin Panel (port 3001)
```
Admin backend reads same DB tables: users, parlors, posts, tournaments, bookings, etc.
Admin backend has its OWN tables: admin_users, admin_roles, admin_permissions, activity_logs

---

## TECH STACK (never deviate)
| Layer | Tech |
|-------|------|
| Admin Backend | Python FastAPI async, port 8001 |
| Admin DB models | SQLAlchemy 2.0 async, same PostgreSQL DB, read-only on main tables |
| Admin Frontend | React 18 + TypeScript + Vite |
| Styling | Tailwind CSS v3 |
| Components | shadcn/ui (Radix UI based) |
| Charts | Recharts |
| Tables | TanStack Table v8 |
| Data Fetching | TanStack Query (React Query) v5 |
| State | Zustand |
| Forms | React Hook Form + Zod |
| HTTP | Axios |
| Routing | React Router DOM v6 |
| Icons | Lucide React |
| Dates | date-fns |
| Toasts | Sonner (toast notifications) |

---

## FOLDER STRUCTURE
```
admin-microservice/
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app, CORS, routes
│   │   ├── config.py           # Settings (DATABASE_URL, JWT_SECRET, etc.)
│   │   ├── deps.py             # Deps: get_db, get_redis, require_admin_permission
│   │   ├── models/
│   │   │   ├── base.py         # SQLAlchemy async engine + Base
│   │   │   ├── admin_user.py   # AdminUser (separate from app's User)
│   │   │   ├── role.py         # AdminRole + AdminPermission
│   │   │   └── activity_log.py # ActivityLog (all app + admin actions)
│   │   ├── schemas/
│   │   │   ├── auth.py
│   │   │   ├── admin_user.py
│   │   │   ├── role.py
│   │   │   ├── activity.py
│   │   │   └── analytics.py
│   │   ├── routers/
│   │   │   ├── auth.py         # POST /login, /logout, /refresh, /me
│   │   │   ├── users.py        # GET/PATCH/DELETE main app users
│   │   │   ├── parlors.py      # GET/PATCH/DELETE parlors + verify
│   │   │   ├── tournaments.py  # GET/PATCH tournaments
│   │   │   ├── bookings.py     # GET all bookings (tournament + slot)
│   │   │   ├── posts.py        # GET/DELETE posts (moderation)
│   │   │   ├── events.py       # GET/PATCH events
│   │   │   ├── community.py    # GET/PIN/DELETE community posts
│   │   │   ├── analytics.py    # GET charts data + platform stats
│   │   │   ├── activity.py     # GET activity log (all platform actions)
│   │   │   ├── roles.py        # CRUD admin roles + permissions config
│   │   │   ├── notifications.py # POST broadcast to app users
│   │   │   └── settings.py     # GET/PUT platform feature flags
│   │   ├── services/
│   │   │   ├── analytics_service.py
│   │   │   └── activity_service.py
│   │   └── middleware/
│   │       └── activity_logger.py  # Middleware: auto-log every admin action
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── migrations/
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts       # Axios instance, interceptors, token refresh
│   │   │   └── endpoints.ts    # All API functions (typed)
│   │   ├── store/
│   │   │   ├── authStore.ts    # Zustand: admin user, token, permissions
│   │   │   └── uiStore.ts      # Zustand: sidebar collapse, theme
│   │   ├── types/
│   │   │   └── index.ts        # All TypeScript interfaces
│   │   ├── hooks/
│   │   │   ├── useAdminUser.ts
│   │   │   ├── usePermission.ts  # hasPermission('delete_users')
│   │   │   └── useDebounce.ts
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AdminLayout.tsx   # Root layout wrapper
│   │   │   │   ├── Sidebar.tsx       # Left sidebar nav
│   │   │   │   └── Header.tsx        # Top bar with user + notifications
│   │   │   ├── ui/
│   │   │   │   ├── DataTable.tsx     # Reusable TanStack Table
│   │   │   │   ├── StatsCard.tsx     # Metric cards
│   │   │   │   ├── StatusBadge.tsx   # Colored status pill
│   │   │   │   ├── ConfirmDialog.tsx # Delete/action confirm modal
│   │   │   │   ├── SearchFilter.tsx  # Search + filter bar
│   │   │   │   └── Pagination.tsx    # Page controls
│   │   │   ├── charts/
│   │   │   │   ├── LineChart.tsx     # Recharts line
│   │   │   │   ├── BarChart.tsx      # Recharts bar
│   │   │   │   └── PieChart.tsx      # Recharts pie/donut
│   │   │   └── forms/
│   │   │       └── RoleForm.tsx
│   │   ├── pages/
│   │   │   ├── login/LoginPage.tsx
│   │   │   ├── dashboard/DashboardPage.tsx
│   │   │   ├── users/UsersPage.tsx
│   │   │   ├── parlors/ParlorsPage.tsx
│   │   │   ├── tournaments/TournamentsPage.tsx
│   │   │   ├── bookings/BookingsPage.tsx
│   │   │   ├── posts/PostsPage.tsx
│   │   │   ├── events/EventsPage.tsx
│   │   │   ├── community/CommunityPage.tsx
│   │   │   ├── analytics/AnalyticsPage.tsx
│   │   │   ├── activity/ActivityPage.tsx
│   │   │   ├── roles/RolesPage.tsx
│   │   │   ├── notifications/NotificationsPage.tsx
│   │   │   └── settings/SettingsPage.tsx
│   │   ├── App.tsx             # React Router routes
│   │   ├── main.tsx            # Entry point
│   │   └── index.css           # Tailwind directives
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── Dockerfile
│
├── docker-compose.yml
├── GROK_FIRST_SESSION_ADMIN.md  ← THIS FILE
├── PROGRESS_ADMIN.md
└── GROK_DAILY_ADMIN.md
```

---

## DATABASE — ADMIN-SPECIFIC TABLES (create via Alembic)
```sql
-- Admin users (completely separate from main app users table)
admin_users (
  id UUID PK DEFAULT gen_random_uuid(),
  email VARCHAR UNIQUE NOT NULL,
  name VARCHAR NOT NULL,
  password_hash VARCHAR NOT NULL,        -- bcrypt
  role_id UUID → admin_roles,
  is_active BOOL DEFAULT true,
  avatar_url VARCHAR,
  last_login TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  created_by UUID → admin_users          -- who created this admin
)

-- Roles (e.g. super_admin, admin, moderator, support, analyst)
admin_roles (
  id UUID PK,
  name VARCHAR UNIQUE NOT NULL,          -- 'super_admin', 'admin', 'moderator'
  display_name VARCHAR,
  description TEXT,
  color VARCHAR DEFAULT '#8B5CF6',       -- for badge display
  is_system_role BOOL DEFAULT false,     -- system roles cannot be deleted
  created_at TIMESTAMPTZ DEFAULT now()
)

-- Permissions assigned to roles
admin_role_permissions (
  id UUID PK,
  role_id UUID → admin_roles,
  permission VARCHAR NOT NULL,           -- see PERMISSIONS list below
  UNIQUE(role_id, permission)
)

-- Activity log (all platform actions — main app + admin)
activity_logs (
  id UUID PK,
  actor_id UUID NOT NULL,               -- who did it
  actor_type VARCHAR NOT NULL,          -- 'user', 'parlor_owner', 'admin'
  actor_name VARCHAR,                   -- cached name for display
  action VARCHAR NOT NULL,              -- see ACTION TYPES below
  target_type VARCHAR,                  -- 'user','parlor','tournament','post','booking'
  target_id UUID,
  target_name VARCHAR,                  -- cached name for display
  metadata JSONB DEFAULT '{}',          -- extra context
  ip_address VARCHAR,
  user_agent VARCHAR,
  severity VARCHAR DEFAULT 'info',      -- 'info','warning','critical'
  created_at TIMESTAMPTZ DEFAULT now(),
  INDEX(actor_id, created_at DESC),
  INDEX(action, created_at DESC),
  INDEX(target_type, target_id),
  INDEX(severity, created_at DESC)
)

-- Platform settings / feature flags
platform_settings (
  id UUID PK,
  key VARCHAR UNIQUE NOT NULL,
  value JSONB NOT NULL,
  description TEXT,
  updated_by UUID → admin_users,
  updated_at TIMESTAMPTZ DEFAULT now()
)
```

---

## PERMISSIONS LIST (complete, for roles config UI)
```python
PERMISSIONS = [
  # User management
  "users.view",       "users.edit",       "users.delete",     "users.ban",
  "users.export",     "users.change_role",
  # Parlor management
  "parlors.view",     "parlors.verify",   "parlors.delete",   "parlors.edit",
  # Content moderation
  "posts.view",       "posts.delete",
  "comments.view",    "comments.delete",
  "community.view",   "community.delete", "community.pin",
  # Tournaments & Events
  "tournaments.view", "tournaments.edit", "tournaments.cancel","tournaments.delete",
  "events.view",      "events.edit",      "events.cancel",    "events.delete",
  # Bookings
  "bookings.view",    "bookings.cancel",
  # Analytics
  "analytics.view",   "analytics.export",
  # Notifications
  "notifications.send",
  # Roles & Admins
  "roles.view",       "roles.create",     "roles.edit",       "roles.delete",
  "admin_users.view", "admin_users.create","admin_users.edit", "admin_users.delete",
  # Settings
  "settings.view",    "settings.edit",
  # Activity
  "activity.view",    "activity.export",
]

DEFAULT_ROLE_PERMISSIONS = {
  "super_admin": ["*"],            # all permissions
  "admin": PERMISSIONS - ["roles.delete", "admin_users.delete"],
  "moderator": ["users.view","users.ban","posts.view","posts.delete",
                "comments.view","comments.delete","community.view",
                "community.delete","community.pin","parlors.view",
                "tournaments.view","events.view","bookings.view","activity.view"],
  "support": ["users.view","parlors.view","tournaments.view","events.view",
              "bookings.view","posts.view","comments.view","activity.view"],
  "analyst": ["analytics.view","analytics.export","users.view","parlors.view",
              "tournaments.view","bookings.view","activity.view"],
}
```

---

## ACTION TYPES (for activity log)
```python
ACTIVITY_ACTIONS = {
  # App user actions (logged by main backend via shared DB write or queue)
  "user.registered":       "New user registered",
  "user.login":            "User logged in",
  "user.profile_updated":  "Profile updated",
  "parlor.created":        "Parlor registered",
  "parlor.updated":        "Parlor profile updated",
  "tournament.created":    "Tournament created",
  "tournament.status_changed": "Tournament status changed",
  "booking.created":       "Slot booked",
  "booking.cancelled":     "Booking cancelled",
  "post.created":          "Post published",
  "post.deleted":          "Post deleted",
  "comment.created":       "Comment added",
  "comment.deleted":       "Comment deleted",
  "follow.created":        "User followed parlor",
  "like.created":          "User liked content",
  "event.created":         "Event created",
  "event.registration":    "User registered for event",
  "message.sent":          "Message sent",
  "community.post_created": "Community post published",
  # Admin actions (logged by admin backend)
  "admin.login":            "Admin logged in",
  "admin.user_banned":      "Admin banned user",
  "admin.user_unbanned":    "Admin unbanned user",
  "admin.user_deleted":     "Admin deleted user",
  "admin.parlor_verified":  "Admin verified parlor",
  "admin.post_deleted":     "Admin removed post",
  "admin.comment_deleted":  "Admin removed comment",
  "admin.broadcast_sent":   "Admin sent broadcast notification",
  "admin.role_changed":     "Admin changed user role",
  "admin.settings_updated": "Admin updated platform settings",
}
```

---

## ALL ADMIN API ENDPOINTS
```
BASE URL: http://localhost:8001/api (dev)

AUTH:
  POST /api/auth/login           body:{email,password} → {access_token, admin_user}
  POST /api/auth/logout
  POST /api/auth/refresh         body:{refresh_token}
  GET  /api/auth/me

ADMIN USERS (manage admin panel users):
  GET  /api/admin-users          ?page=&search=&role_id=
  POST /api/admin-users          body:{email,name,password,role_id}
  GET  /api/admin-users/{id}
  PUT  /api/admin-users/{id}     body:{name,role_id,is_active}
  DELETE /api/admin-users/{id}

ROLES & PERMISSIONS:
  GET  /api/roles                (all roles + their permissions)
  POST /api/roles                body:{name,display_name,description,color}
  GET  /api/roles/{id}
  PUT  /api/roles/{id}           body:{display_name,description,color}
  DELETE /api/roles/{id}         (only non-system roles)
  PUT  /api/roles/{id}/permissions body:{permissions:["users.view","users.ban",...]}

PLATFORM STATS:
  GET  /api/stats                → all counts + today's deltas

ANALYTICS:
  GET  /api/analytics/users      ?period=7d|30d|90d → daily new user counts
  GET  /api/analytics/bookings   ?period= → daily booking counts + revenue
  GET  /api/analytics/posts      ?period= → posts per day
  GET  /api/analytics/top-parlors?period=&limit=10
  GET  /api/analytics/game-types → pie chart data
  GET  /api/analytics/user-roles → pie chart: user vs parlor_owner distribution
  GET  /api/analytics/revenue    ?period= → revenue trend

APP USERS (main app's users table):
  GET  /api/users                ?page=&search=&role=&is_active=&sort=
  GET  /api/users/{id}           (detailed view + their bookings, follows, posts)
  PATCH /api/users/{id}          body:{is_active,role} (ban/role change)
  DELETE /api/users/{id}

PARLORS:
  GET  /api/parlors              ?page=&search=&is_verified=&sort=followers|rating|date
  GET  /api/parlors/{id}
  PATCH /api/parlors/{id}/verify body:{is_verified}
  DELETE /api/parlors/{id}

TOURNAMENTS:
  GET  /api/tournaments          ?page=&search=&status=&parlor_id=
  GET  /api/tournaments/{id}     (detail + bookings list)
  PATCH /api/tournaments/{id}    body:{status}
  DELETE /api/tournaments/{id}

BOOKINGS:
  GET  /api/bookings             ?page=&type=tournament|slot&status=&parlor_id=&date=
  GET  /api/bookings/{id}
  PATCH /api/bookings/{id}       body:{status:'cancelled'}

POSTS:
  GET  /api/posts                ?page=&search=&parlor_id=
  GET  /api/posts/{id}
  DELETE /api/posts/{id}

EVENTS:
  GET  /api/events               ?page=&status=&parlor_id=
  PATCH /api/events/{id}         body:{status,is_featured}
  DELETE /api/events/{id}

COMMUNITY:
  GET  /api/community            ?page=&tag=&sort=latest|trending
  PATCH /api/community/{id}      body:{is_pinned}
  DELETE /api/community/{id}

ACTIVITY LOG:
  GET  /api/activity             ?page=&actor_type=&action=&severity=&from=&to=&search=
  GET  /api/activity/stats       → action counts grouped by type (for charts)
  GET  /api/activity/export      → CSV download

NOTIFICATIONS BROADCAST:
  POST /api/notifications/broadcast  body:{title,body,target:'all'|'users'|'parlor_owners',data?}

SETTINGS:
  GET  /api/settings             → all feature flags + config
  PUT  /api/settings/{key}       body:{value}
```

---

## REACT PAGES & WHAT EACH SHOWS
```
/login               → Login form (email + password), logo, dark theme
/dashboard           → Stats cards row + 2 line charts (users + bookings) + recent activity list + top parlors
/users               → Table: name/phone/role/status/joined + ban/unban/delete/role actions + search + filters
/parlors             → Table: name/owner/games/rating/followers/verified + verify toggle + delete
/tournaments         → Table: title/game/slots/status/parlor/date + status change + delete
/bookings            → Table: user/parlor/event/slot/status/payment + filter by type (tournament|slot)
/posts               → Table: parlor/content preview/media/likes/comments + delete (moderation)
/events              → Table: title/type/parlor/date/participants/status + feature toggle + cancel + delete
/community           → Table: author/title/tag/likes/comments/pinned + pin toggle + delete
/analytics           → Charts: users growth (line) + bookings trend (line) + revenue (bar) + top parlors (bar) + game distribution (pie) + role distribution (pie)
/activity            → Table: actor/action/target/severity/ip/time + filter by action/severity/date range + export CSV
/roles               → Role cards: name/color/permissions count + click to edit permissions (checkbox grid)
/notifications       → Broadcast form: title + body + target radio + send button + history of past broadcasts
/settings            → Feature flag toggles + platform config key-value editor
```

---

## PERMISSION GUARD PATTERN (use everywhere)
```tsx
// In any component:
const { hasPermission } = usePermission();

// Hide/show based on permission:
{hasPermission('users.ban') && <BanButton />}
{hasPermission('analytics.view') && <AnalyticsPage />}

// In sidebar nav — filter items by permission:
const navItems = ALL_NAV_ITEMS.filter(item => hasPermission(item.requiredPermission));
```

---

## REACT COMPONENT PATTERNS
```tsx
// Every page follows this pattern:
export default function UsersPage() {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState({});

  const { data, isLoading } = useQuery({
    queryKey: ['users', page, search, filters],
    queryFn: () => api.getUsers({ page, search, ...filters }),
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteUser,
    onSuccess: () => { queryClient.invalidateQueries(['users']); toast.success('Deleted'); },
    onError: (e) => toast.error(e.message),
  });

  return (
    <div>
      <PageHeader title="Users" count={data?.total} />
      <SearchFilter onSearch={setSearch} filters={...} />
      <DataTable columns={columns} data={data?.items} isLoading={isLoading} />
      <Pagination page={page} total={data?.pages} onChange={setPage} />
    </div>
  );
}
```

---

## ENVIRONMENT VARIABLES
```bash
# backend/.env
DATABASE_URL=postgresql+asyncpg://gameconnect:password@localhost:5432/gameconnect
REDIS_URL=redis://localhost:6379
ADMIN_JWT_SECRET=admin-super-secret-key-different-from-main-app
ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_REFRESH_TOKEN_EXPIRE_DAYS=7
MAIN_APP_URL=http://localhost:8000   # for cross-service calls if needed
ALLOWED_ORIGINS=http://localhost:3001,https://admin.parlour.in

# frontend/.env
VITE_API_URL=http://localhost:8001/api
VITE_APP_NAME=GameConnect Admin
```

---

## CODING RULES
1. FastAPI: async/await everywhere. Permission deps: `Depends(require_permission('users.view'))`.
2. SQLAlchemy 2.0: `select()` not `session.query()`. `await db.commit()`.
3. Pydantic v2: `model_config = ConfigDict(from_attributes=True)`.
4. React: TypeScript everywhere. No `any`. Proper interfaces for all API responses.
5. TanStack Query: `queryKey` arrays must include all filter params.
6. Mutations: always `queryClient.invalidateQueries()` on success.
7. Toasts: success toast after every mutation. Error toast on failure.
8. Tables: use DataTable.tsx wrapper (not raw TanStack Table) for consistency.
9. Permissions: every sensitive action wrapped in `hasPermission()` check.
10. Activity logging: every admin action must call `activity_service.log_action()`.
11. New DB table = `alembic revision --autogenerate -m "name"` + `alembic upgrade head`.

---

## FIRST COMMANDS TO RUN
```bash
# Backend setup:
cd admin-microservice/backend
pip install -r requirements.txt
cp .env.example .env  # fill in values
alembic upgrade head  # create admin tables
python -m app.seed    # create first super_admin user

# Frontend setup:
cd admin-microservice/frontend
npm install
npm run dev           # runs on localhost:3001

# Or via Docker:
docker compose up --build
# Frontend: http://localhost:3001
# Backend API: http://localhost:8001
# Swagger: http://localhost:8001/docs
```

---

## SESSION INSTRUCTIONS FOR GROK
1. Run: `find . -type f -name "*.py" -o -name "*.tsx" -o -name "*.ts" | grep -v node_modules | grep -v __pycache__ | sort`
2. Run: `cat PROGRESS_ADMIN.md | grep "^\- \[ \]" | head -10`
3. Find first unchecked `[ ]` task
4. Read related existing files before writing
5. Build completely — full file code, no truncation
6. Run install commands if new packages needed
7. Create Alembic migration for any new DB models
8. Mark task `[x] DONE YYYY-MM-DD` in PROGRESS_ADMIN.md
9. Continue to next task without waiting
