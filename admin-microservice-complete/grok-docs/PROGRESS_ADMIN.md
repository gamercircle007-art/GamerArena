# ADMIN MICROSERVICE — PROGRESS TRACKER
# Grok: `cat PROGRESS_ADMIN.md | grep "^\- \[ \]" | head -5` → build next task → mark [x] DONE → continue
# ════════════════════════════════════════════════════════════════════════════════

## QUICK COMMANDS
```bash
cd admin-microservice/backend
uvicorn app.main:app --port 8001 --reload      # run backend
alembic upgrade head                            # apply migrations

cd admin-microservice/frontend
npm run dev                                     # run frontend on :3001
npm run build                                   # production build
```

---

## PHASE 1 — BACKEND FOUNDATION

### Project Setup
- [ ] AM-B01: Create backend/requirements.txt with all packages
      fastapi uvicorn[standard] sqlalchemy[asyncio] asyncpg alembic pydantic-settings
      pydantic[email] python-jose[cryptography] passlib[bcrypt] redis httpx
      python-multipart pytest pytest-asyncio slowapi
- [ ] AM-B02: Create backend/app/config.py (pydantic-settings)
      Fields: DATABASE_URL, REDIS_URL, ADMIN_JWT_SECRET, ADMIN_ACCESS_TOKEN_EXPIRE_MINUTES=60,
              ADMIN_REFRESH_TOKEN_EXPIRE_DAYS=7, ALLOWED_ORIGINS, MAIN_APP_URL
- [ ] AM-B03: Create backend/app/models/base.py
      SQLAlchemy async engine + SessionLocal + Base class
- [ ] AM-B04: Create backend/app/main.py
      FastAPI app + CORS (from config) + include all routers at /api prefix
      Add: startup event, health endpoint GET /health
- [ ] AM-B05: Create backend/.env.example and backend/Dockerfile
- [ ] AM-B06: Create backend/alembic.ini + alembic env.py (point to same DB as main app)

### Admin DB Models
- [ ] AM-B07: Create backend/app/models/admin_user.py
      AdminUser: id(UUID), email(unique), name, password_hash, role_id→admin_roles,
                 is_active, avatar_url, last_login, created_at, created_by→admin_users

- [ ] AM-B08: Create backend/app/models/role.py
      AdminRole: id, name(unique), display_name, description, color, is_system_role, created_at
      AdminRolePermission: id, role_id→admin_roles, permission(VARCHAR), UNIQUE(role_id,permission)

- [ ] AM-B09: Create backend/app/models/activity_log.py
      ActivityLog: id, actor_id(UUID), actor_type, actor_name, action, target_type,
                   target_id, target_name, metadata(JSONB), ip_address, user_agent,
                   severity(info/warning/critical), created_at
      Add indexes: (actor_id, created_at), (action, created_at), (severity, created_at)

- [ ] AM-B10: Create backend/app/models/platform_settings.py
      PlatformSetting: id, key(unique), value(JSONB), description, updated_by, updated_at

- [ ] AM-B11: Run Alembic migration
      `alembic revision --autogenerate -m "create_admin_tables"`
      `alembic upgrade head`
      Verify tables exist in DB: admin_users, admin_roles, admin_role_permissions, activity_logs, platform_settings

### Seed Data
- [ ] AM-B12: Create backend/app/seed.py
      Create system roles with default permissions (see PERMISSIONS in GROK_FIRST_SESSION_ADMIN.md):
        super_admin, admin, moderator, support, analyst
      Create first super_admin user:
        email: admin@parlour.in, password: Admin@1234 (force change on first login)
      Create default platform_settings:
        {allow_new_parlors: true, allow_paid_tournaments: false, community_enabled: true,
         messaging_enabled: false, max_radius_km: 50, platform_commission_pct: 10}
      Run: `python -m app.seed`

### Auth Backend
- [ ] AM-B13: Create backend/app/deps.py
      get_db() → AsyncSession
      get_admin_user(token) → AdminUser (verify JWT, check is_active)
      require_permission(permission: str) → Callable that checks role permissions
      get_client_ip(request) → str

- [ ] AM-B14: Create backend/app/schemas/auth.py
      LoginRequest: email, password
      TokenResponse: access_token, refresh_token, token_type, admin_user (nested)
      AdminUserMeResponse: id, email, name, role{id,name,display_name,color}, permissions[], avatar_url, last_login

- [ ] AM-B15: Create backend/app/routers/auth.py
      POST /api/auth/login → verify email+bcrypt password → return JWT pair + log admin.login activity
      POST /api/auth/logout → (invalidate refresh token if storing in Redis)
      POST /api/auth/refresh → rotate tokens
      GET  /api/auth/me → return current admin user + role + permissions[]
      POST /api/auth/change-password body:{current_password, new_password}

### Activity Service
- [ ] AM-B16: Create backend/app/services/activity_service.py
      log_action(db, actor_id, actor_type, actor_name, action, target_type=None,
                 target_id=None, target_name=None, metadata={}, ip=None, severity='info')
      Writes to activity_logs table. Call this from every admin action.

### Admin Users CRUD
- [ ] AM-B17: Create backend/app/schemas/admin_user.py
      AdminUserCreate: email, name, password, role_id
      AdminUserUpdate: name, role_id, is_active, avatar_url
      AdminUserResponse: id, email, name, role{...}, is_active, last_login, created_at

- [ ] AM-B18: Create backend/app/routers/admin_users.py
      GET  /api/admin-users?page=&search=&role_id=    (require: admin_users.view)
      POST /api/admin-users                            (require: admin_users.create)
      GET  /api/admin-users/{id}
      PUT  /api/admin-users/{id}                       (require: admin_users.edit)
      DELETE /api/admin-users/{id}                     (require: admin_users.delete, cannot delete self)

### Roles CRUD
- [ ] AM-B19: Create backend/app/schemas/role.py
      RoleCreate: name, display_name, description, color
      RolePermissionsUpdate: permissions: List[str]
      RoleResponse: id, name, display_name, description, color, is_system_role, permissions[], admin_count

- [ ] AM-B20: Create backend/app/routers/roles.py
      GET  /api/roles                    (require: roles.view) → all roles + permission lists
      POST /api/roles                    (require: roles.create)
      GET  /api/roles/{id}
      PUT  /api/roles/{id}               (require: roles.edit)
      DELETE /api/roles/{id}             (require: roles.delete, block if is_system_role=true)
      PUT  /api/roles/{id}/permissions   (require: roles.edit) body:{permissions:[...]}

### Stats Endpoint
- [ ] AM-B21: Create backend/app/routers/stats.py
      GET /api/stats → AdminStatsResponse:
        total_users, total_parlors, total_tournaments, total_bookings, total_posts,
        total_events, total_community_posts, total_ratings, total_messages,
        new_users_today, new_users_week, new_bookings_today, new_bookings_week,
        active_tournaments, pending_verification (parlors), active_admins,
        revenue_today, revenue_this_month
      No permission guard (all authenticated admins can see stats)

### Analytics Endpoints
- [ ] AM-B22: Create backend/app/services/analytics_service.py
      get_daily_counts(model, date_col, days, db) → List[{date, count}]
      get_top_parlors(days, limit, db) → List[{parlor_id, name, bookings, revenue}]
      get_game_distribution(db) → List[{game_type, count}]
      get_user_role_distribution(db) → List[{role, count}]

- [ ] AM-B23: Create backend/app/routers/analytics.py
      All require: analytics.view
      GET /api/analytics/users?period=7d|30d|90d
      GET /api/analytics/bookings?period=
      GET /api/analytics/posts?period=
      GET /api/analytics/revenue?period=
      GET /api/analytics/top-parlors?period=&limit=10
      GET /api/analytics/game-types        → pie data
      GET /api/analytics/user-roles        → pie data
      GET /api/analytics/booking-status    → pie data
      GET /api/analytics/activity-by-type?period= → bar data

### Activity Log Endpoints
- [ ] AM-B24: Create backend/app/schemas/activity.py
      ActivityLogItem: id, actor_name, actor_type, action, target_type, target_name,
                       metadata, ip_address, severity, created_at
      ActivityStatsResponse: List[{action, count}]

- [ ] AM-B25: Create backend/app/routers/activity.py
      All require: activity.view
      GET /api/activity?page=&actor_type=&action=&severity=&from=&to=&search=
      GET /api/activity/stats?period=7d → counts per action type
      GET /api/activity/export → StreamingResponse CSV (require: activity.export)

### App Data Routers (read main app tables)
- [ ] AM-B26: Create backend/app/routers/users.py
      GET /api/users?page=&search=&role=&is_active=   (require: users.view)
      GET /api/users/{id}                              (full detail + bookings + follows + posts count)
      PATCH /api/users/{id}    body:{is_active,role}   (require: users.ban or users.change_role)
        → log admin.user_banned/unbanned/role_changed activity
      DELETE /api/users/{id}                           (require: users.delete)

- [ ] AM-B27: Create backend/app/routers/parlors.py (read main app parlors)
      GET /api/parlors?page=&search=&is_verified=&sort= (require: parlors.view)
      GET /api/parlors/{id}
      PATCH /api/parlors/{id}/verify                    (require: parlors.verify)
        → log admin.parlor_verified activity
      DELETE /api/parlors/{id}                          (require: parlors.delete)

- [ ] AM-B28: Create backend/app/routers/tournaments.py (require: tournaments.view)
      GET /api/tournaments, GET /api/tournaments/{id}
      PATCH /api/tournaments/{id} (require: tournaments.edit)
      DELETE /api/tournaments/{id} (require: tournaments.delete)

- [ ] AM-B29: Create backend/app/routers/posts.py (require: posts.view)
      GET /api/posts, DELETE /api/posts/{id} (require: posts.delete → log activity)

- [ ] AM-B30: Create backend/app/routers/bookings.py (require: bookings.view)
      GET /api/bookings?type=tournament|slot&page=&status=&date=
      PATCH /api/bookings/{id} body:{status:'cancelled'} (require: bookings.cancel)

- [ ] AM-B31: Create backend/app/routers/events.py, community.py, notifications.py, settings.py
      Events: GET/PATCH/DELETE (require: events.view/edit/delete)
      Community: GET/PATCH (pin)/DELETE (require: community.view/pin/delete)
      Notifications: POST /api/notifications/broadcast (require: notifications.send)
      Settings: GET /api/settings (require: settings.view), PUT /api/settings/{key} (require: settings.edit)

---

## PHASE 2 — FRONTEND SETUP

### Project Init
- [ ] AM-F01: Create frontend/package.json with all dependencies:
      react@18, react-dom, react-router-dom@6, typescript, vite,
      @tanstack/react-query@5, @tanstack/react-table@8, zustand,
      axios, react-hook-form, @hookform/resolvers, zod,
      recharts, lucide-react, date-fns, sonner,
      tailwindcss, @tailwindcss/forms, autoprefixer, postcss,
      @radix-ui/react-dialog, @radix-ui/react-dropdown-menu,
      @radix-ui/react-select, @radix-ui/react-checkbox,
      @radix-ui/react-tabs, @radix-ui/react-tooltip,
      clsx, tailwind-merge, class-variance-authority
      Run: `npm install`

- [ ] AM-F02: Create frontend/vite.config.ts
      Port 3001, proxy /api → localhost:8001, resolve aliases @/ → src/

- [ ] AM-F03: Create frontend/tailwind.config.ts
      Extend colors: primary(purple), secondary(cyan), brand palette
      Include shadcn/ui animation utilities

- [ ] AM-F04: Create frontend/tsconfig.json + src/index.css (Tailwind directives)

- [ ] AM-F05: Create frontend/src/types/index.ts
      All TypeScript interfaces: AdminUser, Role, Permission, ActivityLog,
      AppUser, Parlor, Tournament, Booking, Post, Event, CommunityPost,
      PaginatedResponse<T>, AdminStats, AnalyticsDataPoint, etc.

### Core Infrastructure
- [ ] AM-F06: Create frontend/src/api/client.ts
      Axios instance: baseURL from VITE_API_URL
      Request interceptor: attach Bearer token from localStorage
      Response interceptor: 401 → try refresh → retry → else logout
      Export typed api functions

- [ ] AM-F07: Create frontend/src/api/endpoints.ts
      All typed API functions organized by module:
      auth: { login, logout, refresh, me }
      users: { list, get, update, delete }
      parlors: { list, get, verify, delete }
      tournaments: { list, get, update, delete }
      bookings: { list, update }
      posts: { list, delete }
      events: { list, update, delete }
      community: { list, pin, delete }
      analytics: { users, bookings, posts, revenue, topParlors, gameTypes, userRoles }
      activity: { list, stats, export }
      roles: { list, get, create, update, delete, updatePermissions }
      adminUsers: { list, get, create, update, delete }
      notifications: { broadcast }
      settings: { list, update }
      stats: { get }

- [ ] AM-F08: Create frontend/src/store/authStore.ts (Zustand)
      State: adminUser | null, accessToken | null, isAuthenticated
      Actions: login(email, password), logout(), setTokens(), refreshToken()
      Persist to localStorage (token + user)

- [ ] AM-F09: Create frontend/src/store/uiStore.ts (Zustand)
      State: sidebarCollapsed bool
      Actions: toggleSidebar(), setSidebarCollapsed()

- [ ] AM-F10: Create frontend/src/hooks/usePermission.ts
      hasPermission(permission: string): bool
      hasAnyPermission(permissions: string[]): bool
      hasAllPermissions(permissions: string[]): bool
      (reads permissions[] from authStore.adminUser.permissions)

- [ ] AM-F11: Create frontend/src/hooks/useDebounce.ts (300ms debounce for search)

### Layout Components
- [ ] AM-F12: Create frontend/src/components/layout/AdminLayout.tsx
      Full-height flex row: Sidebar (fixed 260px) + main area
      Main: Header (56px fixed top) + scrollable content
      Mobile: sidebar becomes off-canvas drawer (hamburger in header)
      Protected route wrapper (redirect to /login if not authenticated)

- [ ] AM-F13: Create frontend/src/components/layout/Sidebar.tsx
      Logo section at top
      Nav groups with section labels
      NavItem with: icon + label + active highlight + permission guard
      All nav items (filter by hasPermission):
        OVERVIEW: Dashboard (always), Analytics (analytics.view)
        CONTENT MGMT: Users (users.view), Parlors (parlors.view), Tournaments (tournaments.view),
                      Bookings (bookings.view), Posts (posts.view), Events (events.view),
                      Community (community.view)
        PLATFORM: Activity Log (activity.view), Broadcast (notifications.send),
                  Roles (roles.view), Admin Users (admin_users.view), Settings (settings.view)
      Bottom: current admin user avatar + name + logout button
      Collapse toggle (icon-only mode when collapsed)

- [ ] AM-F14: Create frontend/src/components/layout/Header.tsx
      Page title (from current route)
      Right: global search icon + notification bell + admin avatar dropdown
      Avatar dropdown: Profile, Change Password, Logout

### Reusable UI Components
- [ ] AM-F15: Create frontend/src/components/ui/DataTable.tsx
      Generic TanStack Table v8 wrapper
      Props: columns, data, isLoading (shows skeleton), emptyMessage
      Features: row click handler, striped rows, sticky header
      Built-in loading skeleton (3 rows of shimmer)

- [ ] AM-F16: Create frontend/src/components/ui/StatsCard.tsx
      Props: title, value, delta(+N today), icon, color, trend(up|down|neutral)
      Shows: large number + title + delta badge + colored icon container

- [ ] AM-F17: Create frontend/src/components/ui/StatusBadge.tsx
      Props: status string → auto colors (active=green, banned=red, pending=orange, etc.)

- [ ] AM-F18: Create frontend/src/components/ui/ConfirmDialog.tsx
      Radix Dialog: title + message + cancel + confirm (red) buttons
      Props: open, onClose, onConfirm, title, message, confirmLabel, isLoading

- [ ] AM-F19: Create frontend/src/components/ui/SearchFilter.tsx
      Search input (debounced 300ms) + filter dropdowns (role, status, etc.)
      Props: onSearch, filters: FilterConfig[], onFilterChange

- [ ] AM-F20: Create frontend/src/components/ui/Pagination.tsx
      Page X of Y + prev/next buttons + "showing N-M of total"

- [ ] AM-F21: Create frontend/src/components/ui/PageHeader.tsx
      Title + optional subtitle + total count badge + action buttons slot

### Chart Components
- [ ] AM-F22: Create frontend/src/components/charts/LineChart.tsx
      Recharts ResponsiveContainer + LineChart
      Props: data [{date, value}], color, label, height
      Tooltip: "X on date"

- [ ] AM-F23: Create frontend/src/components/charts/BarChart.tsx
      Recharts bar chart
      Props: data [{name, value}], color, label, height, horizontal(bool)

- [ ] AM-F24: Create frontend/src/components/charts/PieChart.tsx
      Recharts Pie with donut style
      Props: data [{name, value, color}], label, height
      Center text: total number

---

## PHASE 3 — FRONTEND PAGES

### Auth
- [ ] AM-P01: Create frontend/src/pages/login/LoginPage.tsx
      Dark full-screen layout (bg-slate-900)
      Center card: logo + "Admin Panel" + email + password + login button
      React Hook Form + Zod validation
      On submit: authStore.login(email, password) → redirect to /dashboard
      Error: "Invalid credentials" toast
      Loading: button spinner

- [ ] AM-P02: Create frontend/src/App.tsx
      React Router v6 routes:
      / → redirect to /dashboard
      /login → LoginPage (no auth guard)
      /* → AdminLayout wrapping all protected routes:
        /dashboard, /users, /parlors, /tournaments, /bookings,
        /posts, /events, /community, /analytics, /activity,
        /roles, /admin-users, /notifications, /settings
      QueryClientProvider + Toaster at root

### Dashboard
- [ ] AM-P03: Create frontend/src/pages/dashboard/DashboardPage.tsx
      Section 1 — Stats Grid (8 cards, 4-col on desktop):
        Total Users (+N today), Total Parlors (N pending verify),
        Active Tournaments, Total Bookings (+N today),
        Total Posts, Revenue Today, Community Posts, Activity Today
      Section 2 — Charts Row (2 side by side):
        Left: LineChart "New Users (30 days)" data from GET /api/analytics/users
        Right: LineChart "Bookings (30 days)" from GET /api/analytics/bookings
      Section 3 — Charts Row 2:
        Left: BarChart "Top 10 Parlors by Bookings"
        Right: PieChart "User Role Distribution" (user vs parlor_owner)
      Section 4 — Recent Activity (last 20 items from /api/activity):
        Mini list: actor icon + "{actor} {action} {target}" + time ago
      Section 5 — Quick Actions:
        Pending Verifications (N) → go to /parlors?is_verified=false
        Broadcast Notification → go to /notifications
        View Analytics → go to /analytics

### Main Data Pages (each follows same pattern)
- [ ] AM-P04: frontend/src/pages/users/UsersPage.tsx
      Columns: Avatar+Name, Phone/Email, Role(badge), Status(badge), Parlor(if owner), Joined, Actions
      Actions: Ban/Unban toggle, Change Role (dropdown), Delete (confirm dialog)
      Filters: search + role dropdown + is_active dropdown
      Permission guards: ban requires users.ban, delete requires users.delete

- [ ] AM-P05: frontend/src/pages/parlors/ParlorsPage.tsx
      Columns: Logo+Name, Owner, Game Types (chips max 3), Rating (stars), Followers, Status(badge), Date, Actions
      Actions: Verify/Unverify toggle, Delete (confirm)
      Filters: search + is_verified dropdown
      Click row → expanded detail panel (posts count, tournaments count, events count)

- [ ] AM-P06: frontend/src/pages/tournaments/TournamentsPage.tsx
      Columns: Title, Parlor, Game Type, Slots (X/Y), Entry Fee, Start Date, Status(badge), Actions
      Actions: Status change (dropdown: open/live/completed/cancelled), Delete
      Filters: search + status dropdown + parlor search

- [ ] AM-P07: frontend/src/pages/bookings/BookingsPage.tsx
      Tabs: Tournament Bookings | Time Slot Bookings
      Columns: User, Parlor, Event/Slot, Slot#, Status, Payment, Date
      Filters: date range, status, parlor

- [ ] AM-P08: frontend/src/pages/posts/PostsPage.tsx (moderation)
      Columns: Parlor, Content Preview (truncated 100 chars), Images, Likes, Comments, Date, Actions
      Actions: Delete (confirm + log activity)
      Expand row to see full content + media thumbnail

- [ ] AM-P09: frontend/src/pages/events/EventsPage.tsx
      Columns: Cover, Title, Type(badge), Parlor, Date, Entry Fee, Participants X/Y, Featured(toggle), Status, Actions
      Actions: Feature toggle, Status change, Delete

- [ ] AM-P10: frontend/src/pages/community/CommunityPage.tsx
      Columns: Author, Title, Tag(chip), Likes, Comments, Views, Pinned(toggle), Date, Actions
      Actions: Pin/Unpin toggle, Delete

### Analytics Page
- [ ] AM-P11: frontend/src/pages/analytics/AnalyticsPage.tsx
      Period selector: 7d | 30d | 90d (SegmentedControl at top)
      Row 1: LineChart(Users) + LineChart(Bookings)
      Row 2: LineChart(Posts) + BarChart(Revenue per week)
      Row 3: BarChart(Top 10 Parlors) full width
      Row 4: PieChart(Game Type Distribution) + PieChart(User Role Distribution) + PieChart(Booking Status)
      Row 5: BarChart(Activity by Type) full width
      All charts re-fetch when period changes
      Export button: downloads analytics as CSV

### Activity Log Page
- [ ] AM-P12: frontend/src/pages/activity/ActivityPage.tsx
      Filter bar: search actor/action + severity dropdown + action type dropdown + date range picker
      Table columns: Severity(badge), Actor (type badge + name), Action (colored), Target, IP, Time
      Severity colors: info=blue, warning=orange, critical=red
      Row expand: shows metadata JSON + user_agent
      Export CSV button (require: activity.export)
      Live refresh toggle (poll every 30s)

### Role Management Page (most complex)
- [ ] AM-P13: frontend/src/pages/roles/RolesPage.tsx
      Left panel: Role list cards
        - Role card: color swatch + name + display name + N permissions + N admins
        - Highlight selected role
        - Create New Role button (require: roles.create)
        - Delete role button (only non-system roles, require: roles.delete)
      Right panel: Permission editor for selected role
        - Role details form: display_name, description, color picker
        - Save button
        - Permission grid (grouped by category):
          GROUP: User Management → checkboxes: view, edit, delete, ban, export, change_role
          GROUP: Parlor Management → view, verify, edit, delete
          GROUP: Content Moderation → posts.view/delete, comments.view/delete, community.view/delete/pin
          GROUP: Tournaments & Events → all tournament + event permissions
          GROUP: Bookings → view, cancel
          GROUP: Analytics → view, export
          GROUP: Platform → notifications.send, roles.*, admin_users.*, settings.*
          GROUP: Activity → view, export
        - Save Permissions button (require: roles.edit)
        - "Select All" / "Clear All" toggles per group

### Admin Users Page
- [ ] AM-P14: frontend/src/pages/admin-users/AdminUsersPage.tsx (require: admin_users.view)
      Columns: Avatar+Name, Email, Role(badge), Status, Last Login, Created, Actions
      Actions: Edit role + is_active, Delete
      Create Admin button → modal form: name, email, password, role select
      Cannot delete yourself or super_admin users

### Notifications Broadcast Page
- [ ] AM-P15: frontend/src/pages/notifications/NotificationsPage.tsx
      Broadcast form:
        Target: All Users | Gamers Only | Parlor Owners (radio)
        Title: text input
        Message: textarea
        Preview: shows how it'll look on device
        Send button → POST /api/notifications/broadcast
        Success: "Sent to N users!" toast
      Past Broadcasts:
        Table of past broadcasts from activity_logs where action='admin.broadcast_sent'
        Columns: title, target, sent_to count, sent_at, sent_by

### Settings Page
- [ ] AM-P16: frontend/src/pages/settings/SettingsPage.tsx (require: settings.view)
      Feature Flags section (toggles):
        - Allow new parlor registrations
        - Allow paid tournaments (Razorpay)
        - Community posts enabled
        - Direct messaging enabled
        - Geo discovery enabled
      Platform Config section:
        - Platform commission % (number input)
        - Max discovery radius (km)
        - Default nearby parlors limit
      Danger Zone:
        - Maintenance mode toggle (shows maintenance page to all app users)
      All changes: PUT /api/settings/{key} + log activity

---

## PHASE 4 — DOCKER + DEPLOYMENT

- [ ] AM-D01: Create backend/Dockerfile
      FROM python:3.12-slim, install deps, copy code, run uvicorn on 8001

- [ ] AM-D02: Create frontend/Dockerfile
      Multi-stage: node:20 build → nginx:alpine serve

- [ ] AM-D03: Create docker-compose.yml
      Services: admin-backend (port 8001), admin-frontend (port 3001)
      Both connect to same postgres network as main app
      Admin backend: env file, depends_on postgres + redis

- [ ] AM-D04: Create nginx.conf for frontend (serve index.html for all routes)

- [ ] AM-D05: Test full stack:
      `docker compose up --build`
      Open http://localhost:3001 → login with admin@parlour.in / Admin@1234
      Verify all pages load and API calls work

---

## PHASE 5 — ADVANCED FEATURES

- [ ] AM-ADV01: Bulk actions on tables (select rows → bulk delete/ban)
- [ ] AM-ADV02: Dark mode toggle (already tailwind dark: classes ready)
- [ ] AM-ADV03: Real-time activity feed (WebSocket from admin backend on ws://localhost:8001/ws)
- [ ] AM-ADV04: Global search (search across users, parlors, tournaments in one box)
- [ ] AM-ADV05: Admin audit trail (who viewed which page, logged in activity_logs)
- [ ] AM-ADV06: Email reports (weekly platform summary via Celery + SMTP)
- [ ] AM-ADV07: Two-factor authentication for admin login (TOTP)
- [ ] AM-ADV08: IP whitelist for admin panel access

---

## SESSION LOG
| Date | Tasks Completed | Next Task | Notes |
|------|----------------|-----------|-------|
| Day 0 | Setup | AM-B01 | Starting fresh — separate microservice |
