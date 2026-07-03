# GROK — ADMIN MICROSERVICE FIRST SESSION
# Paste this ENTIRE file into Grok when starting the admin panel project.
# Separate project from main app. React + TypeScript + Vite + TailwindCSS.
# ─────────────────────────────────────────────────────────────────────────────

You are building a **standalone admin microservice** for GameConnect/ParLour.
This is a completely SEPARATE project from the main Flutter app.
It runs on its own port/subdomain: admin.parlour.in

## SCAN EXISTING PROJECT FIRST
```bash
find . -type f \( -name "*.tsx" -o -name "*.ts" -o -name "*.json" \) | grep -v node_modules | grep -v dist | sort
cat PROGRESS_ADMIN.md
cat package.json 2>/dev/null || echo "No package.json yet"
```

---

## TECH STACK (never change)
| Layer | Technology |
|-------|-----------|
| Framework | React 18 + TypeScript |
| Build | Vite 5 |
| Styling | TailwindCSS 3 + shadcn/ui components |
| Routing | React Router v6 |
| State | Zustand (auth/global) + TanStack Query v5 (server state) |
| HTTP | Axios with JWT interceptor |
| Tables | TanStack Table v8 (sorting, filtering, pagination) |
| Charts | Recharts 2 (line, bar, pie, area charts) |
| Icons | Lucide React |
| Forms | React Hook Form + Zod validation |
| Date | date-fns |
| Notifications | react-hot-toast |
| Auth | JWT (access + refresh) stored in localStorage |

---

## PROJECT STRUCTURE
```
admin-microservice/
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.ts              # Axios instance + JWT interceptor
│   │   │   ├── auth.api.ts            # Login, logout, refresh
│   │   │   └── admin.api.ts           # All admin API calls
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── AdminLayout.tsx    # Shell: sidebar + topbar + content
│   │   │   │   ├── Sidebar.tsx        # Nav sidebar with role-filtered items
│   │   │   │   └── TopBar.tsx         # Search + notifications + user menu
│   │   │   ├── ui/
│   │   │   │   ├── StatCard.tsx       # KPI card with icon + trend
│   │   │   │   ├── DataTable.tsx      # TanStack Table wrapper (sort+filter+page)
│   │   │   │   ├── StatusBadge.tsx    # Colored status pill
│   │   │   │   ├── ConfirmModal.tsx   # Reusable confirm dialog
│   │   │   │   ├── PageHeader.tsx     # Title + breadcrumb + actions
│   │   │   │   └── Pagination.tsx     # Table pagination controls
│   │   │   └── charts/
│   │   │       ├── AreaChartCard.tsx  # Area line chart card
│   │   │       ├── BarChartCard.tsx   # Bar chart card
│   │   │       └── PieChartCard.tsx   # Pie/donut chart card
│   │   ├── context/
│   │   │   └── AuthContext.tsx        # Auth state + login/logout
│   │   ├── hooks/
│   │   │   ├── useAuth.ts             # Access auth context
│   │   │   └── usePermissions.ts      # Check role permissions
│   │   ├── pages/
│   │   │   ├── auth/LoginPage.tsx
│   │   │   ├── dashboard/DashboardPage.tsx
│   │   │   ├── users/UsersPage.tsx
│   │   │   ├── users/UserDetailPage.tsx
│   │   │   ├── parlors/ParlorsPage.tsx
│   │   │   ├── parlors/ParlorDetailPage.tsx
│   │   │   ├── tournaments/TournamentsPage.tsx
│   │   │   ├── bookings/BookingsPage.tsx
│   │   │   ├── posts/PostsPage.tsx
│   │   │   ├── events/EventsPage.tsx
│   │   │   ├── community/CommunityPage.tsx
│   │   │   ├── analytics/AnalyticsPage.tsx
│   │   │   ├── roles/RolesPage.tsx     # Role + permission config
│   │   │   ├── notifications/NotificationsPage.tsx
│   │   │   └── settings/SettingsPage.tsx
│   │   ├── types/index.ts             # All TypeScript types
│   │   ├── utils/
│   │   │   ├── permissions.ts         # RBAC roles + permissions config
│   │   │   └── formatters.ts          # Date, currency, number formatters
│   │   ├── App.tsx                    # Router setup
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── Dockerfile
├── docker-compose.yml
├── GROK_ADMIN_FIRST_SESSION.md   ← this file
└── PROGRESS_ADMIN.md
```

---

## ROLE + PERMISSION SYSTEM (CRITICAL — build exactly as specified)

### Roles (4 levels)
```typescript
type Role = 'super_admin' | 'admin' | 'parlor_owner' | 'user';
```

### All Permissions
```typescript
// users
VIEW_USERS, CREATE_USERS, EDIT_USERS, DELETE_USERS, BAN_USERS, CHANGE_ROLE
// parlors
VIEW_PARLORS, VERIFY_PARLORS, EDIT_PARLORS, DELETE_PARLORS
// content
VIEW_POSTS, DELETE_POSTS, VIEW_COMMENTS, DELETE_COMMENTS
VIEW_COMMUNITY, DELETE_COMMUNITY, PIN_COMMUNITY
// tournaments
VIEW_TOURNAMENTS, EDIT_TOURNAMENTS, DELETE_TOURNAMENTS
// bookings
VIEW_ALL_BOOKINGS, VIEW_OWN_BOOKINGS
// events
VIEW_EVENTS, EDIT_EVENTS, DELETE_EVENTS
// analytics
VIEW_PLATFORM_ANALYTICS, VIEW_OWN_ANALYTICS, VIEW_REVENUE
// notifications
SEND_BROADCAST
// roles
MANAGE_ROLES, VIEW_ROLES
// settings
MANAGE_SETTINGS
```

### Permission Matrix
| Permission | super_admin | admin | parlor_owner | user |
|---|---|---|---|---|
| All user permissions | ✅ | ✅ | ❌ | ❌ |
| Delete users | ✅ | ✅ | ❌ | ❌ |
| Ban users | ✅ | ✅ | ❌ | ❌ |
| Change user role | ✅ | ❌ | ❌ | ❌ |
| Verify parlors | ✅ | ✅ | ❌ | ❌ |
| Delete parlors | ✅ | ✅ | ❌ | ❌ |
| Platform analytics | ✅ | ✅ | ❌ | ❌ |
| Own analytics | ✅ | ✅ | ✅ | ❌ |
| Revenue data | ✅ | ✅ | ❌ | ❌ |
| Send broadcast | ✅ | ✅ | ❌ | ❌ |
| Manage roles | ✅ | ❌ | ❌ | ❌ |
| Manage settings | ✅ | ❌ | ❌ | ❌ |
| View own bookings | ✅ | ✅ | ✅ | ❌ |

### Access Rule: Non-admin roles
- `user` role: NO access to admin panel at all → redirect to main app
- `parlor_owner`: access ONLY to: own analytics, own bookings, own events, own parlor settings
- `admin`: access to everything EXCEPT: manage roles, change to super_admin, system settings
- `super_admin`: full unrestricted access

---

## API ENDPOINTS (connects to main FastAPI backend)
```
BASE_URL: http://localhost:8000/v1    (or VITE_API_URL env var)

AUTH:
  POST /auth/verify-otp       → {access_token, refresh_token, user}
  POST /auth/google            → {access_token, refresh_token, user}
  POST /auth/refresh           → {access_token}

ADMIN (all require admin/super_admin JWT):
  GET  /admin/stats
  GET  /admin/users            ?page=&limit=&search=&role=&is_active=
  GET  /admin/users/{id}
  PATCH /admin/users/{id}      body:{is_active?, role?}
  DELETE /admin/users/{id}
  GET  /admin/parlors          ?page=&search=&is_verified=
  PATCH /admin/parlors/{id}/verify  body:{is_verified}
  DELETE /admin/parlors/{id}
  GET  /admin/tournaments      ?page=&search=&status=
  PATCH /admin/tournaments/{id}/status  body:{status}
  DELETE /admin/tournaments/{id}
  GET  /admin/posts            ?page=&search=
  DELETE /admin/posts/{id}
  GET  /admin/comments         ?page=&is_deleted=
  DELETE /admin/comments/{id}
  GET  /admin/events           ?page=&status=
  DELETE /admin/events/{id}
  GET  /admin/community        ?page=
  PATCH /admin/community/{id}/pin  body:{is_pinned}
  DELETE /admin/community/{id}
  GET  /admin/ratings          ?page=
  DELETE /admin/ratings/{id}
  POST /admin/notifications/broadcast  body:{title,body,target,type}
  GET  /admin/analytics        ?period=7d|30d|90d
  GET  /admin/bookings         ?page=&type=tournament|slot

PARLOR OWNER (requires parlor_owner JWT):
  GET  /parlors/me/analytics
  GET  /parlors/me/slot-bookings
  GET  /parlors/{id}/events
  GET  /parlors/{id}
```

---

## DASHBOARD WIDGETS + CHARTS
```
Dashboard Page shows:
1. KPI Cards (top row):
   - Total Users | Total Parlors | Active Tournaments | Today's Bookings
   - New Users Today | Pending Verification | Total Posts | Platform Revenue

2. Charts Row 1:
   - User Growth (AreaChart, 30 days)
   - Daily Bookings (BarChart, 30 days)

3. Charts Row 2:
   - Game Type Distribution (PieChart/Donut)
   - Top Parlors by Bookings (horizontal BarChart)

4. Recent Activity Feed:
   - Latest 10 user registrations
   - Latest 10 tournament bookings
   - Latest 5 new parlors

5. Quick Actions:
   - Pending Verification queue (parlors needing verify)
   - Reported Content queue (posts/comments flagged)
```

---

## DESIGN SYSTEM
```css
Colors:
  primary: #6366F1 (indigo-500)
  primary-dark: #4F46E5 (indigo-600)
  secondary: #8B5CF6 (violet-500)
  success: #10B981 (emerald-500)
  warning: #F59E0B (amber-500)
  danger: #EF4444 (red-500)
  sidebar-bg: #1E293B (slate-800)
  sidebar-active: #6366F1
  page-bg: #F1F5F9 (slate-100)
  card-bg: #FFFFFF
  text-primary: #1E293B (slate-800)
  text-secondary: #64748B (slate-500)
  border: #E2E8F0 (slate-200)

Typography:
  font-family: Inter (Google Fonts)
  heading: 24px bold / 20px semibold / 16px semibold
  body: 14px regular / 13px regular
  caption: 12px regular

Spacing: 4px base unit (4, 8, 12, 16, 20, 24, 32, 40, 48)
Border radius: card=12px, button=8px, badge=20px, input=8px
Shadows: card: 0 1px 3px rgba(0,0,0,0.1)
```

---

## CODING RULES (follow strictly)
1. TypeScript everywhere. No `any` types — use proper interfaces.
2. React Query for all API calls (useQuery, useMutation). No useEffect for data fetching.
3. Zustand for auth state only. React Query handles server state.
4. Every page checks permissions with `usePermissions()` hook before rendering actions.
5. DataTable wrapper around TanStack Table — consistent across all pages.
6. All dates formatted with date-fns `format(date, 'dd MMM yyyy')`.
7. All currency formatted as `₹X,XXX` (Indian format).
8. Loading state: skeleton shimmer on every data fetch.
9. Empty state: illustration + text on every empty table/list.
10. Error state: retry button on every failed fetch.
11. ConfirmModal before every destructive action (delete, ban).
12. Mobile responsive: sidebar drawer on <768px, persistent on ≥768px.

---

## KEY PACKAGES (install these)
```bash
npm install react-router-dom @tanstack/react-query @tanstack/react-table \
  axios zustand recharts lucide-react react-hot-toast react-hook-form \
  zod @hookform/resolvers date-fns clsx tailwind-merge

npm install -D typescript @types/react @types/react-dom vite \
  @vitejs/plugin-react tailwindcss autoprefixer postcss
```

---

## START: Scan project → read PROGRESS_ADMIN.md → build first unchecked task.
