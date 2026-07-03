# Angular 21 Admin Panel — PROGRESS TRACKER
# Grok: `cat PROGRESS_ANGULAR.md` → first [ ] task → build → mark [x] YYYY-MM-DD → next
# Stack: Angular 21 + Bootstrap 5 + ngx-bootstrap + ngx-datatable + ng2-charts
# ─────────────────────────────────────────────────────────────────────────────

## HOW GROK USES THIS
Start each session: "Read GROK_ANGULAR_CONTEXT.md and PROGRESS_ANGULAR.md. Build next unchecked task."
End each session: "Mark completed tasks [x] with today's date. Update SESSION LOG."

---

## PHASE A — PROJECT SETUP

- [x] A-01: Create Angular 21 project — 29 Jun 2026
      ```bash
      ng new admin-panel --standalone --routing --style=scss
      cd admin-panel
      ```

- [x] A-02: Install all dependencies — 29 Jun 2026
      ```bash
      npm install bootstrap@^5.3.3 ngx-bootstrap@^18.0.0 \
        @swimlane/ngx-datatable@^20.0.0 \
        ng2-charts@^6.0.0 chart.js@^4.4.0 \
        ngx-toastr@^19.0.0 sweetalert2@^11.14.0 \
        @ng-icons/core@^29.4.0 @ng-icons/bootstrap-icons@^29.4.0 \
        ngx-spinner@^17.0.0
      ```

- [x] A-03: Configure styles.scss — 29 Jun 2026
      → Import Bootstrap: `@import 'bootstrap/scss/bootstrap';`
      → Import ngx-datatable theme: `@import "@swimlane/ngx-datatable/index.css"`
      → Import toastr: `@import 'ngx-toastr/toastr'`
      → Add CSS custom properties: --sidebar-bg, --sidebar-width, --primary, etc.
      → Add sidebar animation CSS
      → Add stat card gradient classes
      → Add overall body/layout CSS

- [x] A-04: Configure angular.json — 29 Jun 2026
      → Add Bootstrap CSS to styles array
      → Add ngx-datatable CSS to styles array
      → Add toastr CSS to styles array
      → Add assets configuration

- [x] A-05: Create environments — 29 Jun 2026
      → environment.ts: `apiUrl: 'http://localhost:8000/api/v1'`
      → environment.prod.ts: `apiUrl: 'https://api.parlour.in/api/v1'`

- [x] A-06: Configure app.config.ts — 29 Jun 2026
      → provideRouter(routes, withComponentInputBinding(), withViewTransitions())
      → provideHttpClient(withInterceptors([authInterceptor, loadingInterceptor]))
      → provideAnimations()
      → importProvidersFrom(BsModalServiceModule, ToastrModule.forRoot({...}), NgxSpinnerModule)
      → provideCharts(withDefaultRegisterables())

- [x] A-07: Create core/models/index.ts — 29 Jun 2026
      Interfaces: User, Parlor, Post, Comment, Like, Tournament, Booking, ParlourEvent,
      CommunityPost, Rating, AdminStats, DayCount, AnalyticsData, ParlorStat,
      PaginatedResponse<T>, AuthTokens, AuthResponse, BroadcastRequest,
      Role, Permission, GeoActivity
      → Post must have: media_type: 'text'|'image'|'video'|'reel', geo_lat?, geo_lng?

- [x] A-08: Create core/constants/permissions.ts — 29 Jun 2026
      → ROLES object, PERMISSIONS object, ROLE_PERMISSIONS matrix
      → hasPermission(role, permission): boolean
      → canAccessAdmin(role): boolean

- [x] A-09: Create core/services/auth.service.ts — 29 Jun 2026
      → Signals: currentUser = signal<User|null>(null), isAuthenticated = computed(...)
      → login(phone, otp): Observable<AuthResponse>
      → logout(): void (clear localStorage, navigate to /login)
      → getToken(): string | null
      → isAdmin(): boolean
      → isSuperAdmin(): boolean
      → Initialize: read stored user from localStorage on app start

- [x] A-10: Create core/services/admin-api.service.ts — 29 Jun 2026
      → inject HttpClient
      → private base = `${environment.apiUrl}/admin`
      → getStats(): Observable<AdminStats>
      → getAnalytics(period): Observable<AnalyticsData>
      → getUsers(params): Observable<PaginatedResponse<User>>
      → updateUser(id, data): Observable<User>
      → deleteUser(id): Observable<void>
      → getParlors(params): Observable<PaginatedResponse<Parlor>>
      → verifyParlor(id, verified): Observable<void>
      → deleteParlor(id): Observable<void>
      → getPosts(params): Observable<PaginatedResponse<Post>>
      → deletePost(id): Observable<void>
      → getComments(params): Observable<PaginatedResponse<Comment>>
      → deleteComment(id): Observable<void>
      → getLikes(params): Observable<PaginatedResponse<Like>>
      → getTournaments(params): Observable<PaginatedResponse<Tournament>>
      → getBookings(params): Observable<PaginatedResponse<Booking>>
      → getEvents(params): Observable<PaginatedResponse<ParlourEvent>>
      → getCommunity(params): Observable<PaginatedResponse<CommunityPost>>
      → getRatings(params): Observable<PaginatedResponse<Rating>>
      → broadcast(data): Observable<{sent_to: number}>
      → getGeoActivity(params): Observable<PaginatedResponse<GeoActivity>>

- [x] A-11: Create core/interceptors/auth.interceptor.ts — 29 Jun 2026
      → Functional interceptor (not class-based)
      → Attach Authorization: Bearer {token} to all requests
      → On 401 response: try refresh token → retry → else logout + navigate to /login
      ```typescript
      export const authInterceptor: HttpInterceptorFn = (req, next) => {
        const auth = inject(AuthService);
        const token = auth.getToken();
        const authReq = token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;
        return next(authReq).pipe(
          catchError(err => { if (err.status === 401) auth.logout(); return throwError(() => err); })
        );
      };
      ```

- [x] A-12: Create core/interceptors/loading.interceptor.ts — 29 Jun 2026
      → Show NgxSpinner on every request
      → Hide NgxSpinner when request completes
      → Track concurrent requests count (only hide when count reaches 0)

- [x] A-13: Create core/guards/auth.guard.ts — 29 Jun 2026
      → Functional guard: `inject(AuthService).isAuthenticated() ? true : redirect('/login')`

- [x] A-14: Create core/guards/role.guard.ts — 29 Jun 2026
      → Factory: `roleGuard(requiredRole: string)`
      → Check current user role against required role
      → Redirect to /dashboard if insufficient role

- [x] A-15: Create app.routes.ts with all routes — 29 Jun 2026

---

## PHASE B — LAYOUT SHELL

- [x] B-01: Create layout/admin-layout/admin-layout.component.ts — 29 Jun 2026
      → Standalone component
      → Template: `<app-sidebar> + <app-topbar> + <router-outlet>`
      → Signal: sidebarCollapsed = signal(false)
      → Toggle: toggleSidebar() → flip signal
      → Pass sidebarCollapsed to both sidebar and main content area
      → CSS: `[class.sidebar-collapsed]="sidebarCollapsed()"`

- [x] B-02: Create shared/components/sidebar/sidebar.component.ts — 29 Jun 2026
      DESIGN (Valex-style):
      → Background: #283046 dark blue-grey
      → Logo section: app icon + "GameConnect Admin" + "v1.0" tag
      → Nav items grouped by section (same as Sidebar.tsx from React version)
      → Active item: purple gradient + glow shadow
      → Collapsed state: show icons only (hide text, hide section labels)
      → Animation: [@sidebarState] trigger — 300ms smooth width transition
      → User info footer: avatar + name + role badge + logout button (shown in expanded)
      
      NAV SECTIONS:
      OVERVIEW:    Dashboard (bi-speedometer2), Analytics (bi-bar-chart)
      MANAGEMENT:  Users (bi-people), Parlors (bi-shop), Tournaments (bi-trophy),
                   Bookings (bi-ticket-perforated), Events (bi-calendar-event)
      CONTENT:     Posts (bi-file-text), Reels & Videos (bi-camera-video),
                   Comments (bi-chat), Likes (bi-heart), Community (bi-globe)
      SOCIAL:      Geo Activity (bi-geo-alt), Ratings (bi-star)
      SYSTEM:      Broadcast (bi-megaphone), Roles (bi-shield-check),
                   Settings (bi-gear) [super_admin only]

- [x] B-03: Create shared/components/topbar/topbar.component.ts — 29 Jun 2026
      → Left: hamburger menu button (toggles sidebar) + current page title
      → Center: global search input (bi-search)
      → Right: notification bell (with badge count) + user dropdown
      → User dropdown items: Profile | Change Password | Logout
      → Responsive: full on desktop, icon-only on mobile

- [x] B-04: Create shared/components/stats-card/stats-card.component.ts — 29 Jun 2026
      Props: title, value, icon, color, trend?, subtitle?
      DESIGN (Valex gradient cards):
      ```html
      <div class="card stats-card gradient-{{color}}">
        <div class="card-body">
          <div class="stats-icon"><ng-icon [name]="icon" size="28" /></div>
          <h2 class="stats-value">{{ value }}</h2>
          <p class="stats-title">{{ title }}</p>
          <small *ngIf="trend" class="trend-{{trend >= 0 ? 'up' : 'down'}}">
            ↑ {{ trend }}% vs last period
          </small>
        </div>
      </div>
      ```
      SCSS:
      ```scss
      .gradient-primary { background: linear-gradient(118deg, #7367f0, rgba(115,103,240,.7)); color: white; }
      .gradient-success  { background: linear-gradient(118deg, #28c76f, rgba(40,199,111,.7)); color: white; }
      .gradient-warning  { background: linear-gradient(118deg, #ff9f43, rgba(255,159,67,.7)); color: white; }
      .gradient-danger   { background: linear-gradient(118deg, #ea5455, rgba(234,84,85,.7));  color: white; }
      .gradient-info     { background: linear-gradient(118deg, #00cfe8, rgba(0,207,232,.7));  color: white; }
      ```

- [x] B-05: Create shared/components/status-badge/status-badge.component.ts — 29 Jun 2026
      → Input: status string
      → Output: colored Bootstrap badge
      → active/confirmed/verified → badge-success
      → banned/cancelled/deleted → badge-danger
      → pending/draft → badge-warning
      → live → badge-primary
      → completed → badge-secondary

- [x] B-06: Create shared/pipes/date-format.pipe.ts — 29 Jun 2026
      Create shared/pipes/currency-in.pipe.ts → ₹1,234 (Indian format)
      Create shared/pipes/truncate.pipe.ts → text.substring(0, n) + '...'

- [x] B-07: Create shared/components/page-header/page-header.component.ts — 29 Jun 2026
      → Input: title, subtitle?, breadcrumbs?, actions (ng-content slot)
      → Breadcrumb nav auto-generated

---

## PHASE C — AUTH

- [x] C-01: Create features/auth/login/login.component.ts — 29 Jun 2026
      DESIGN (full-page, Valex-style):
      → Left half: dark gradient background (#283046 to #7367f0) + logo + features list
      → Right half: white card centered
      
      LOGIN CARD:
      → Tabs: "📱 Phone OTP" | "🔑 Password" (if password login exists)
      → Phone OTP flow:
        - +91 prefix input for phone number
        - "Send OTP" button → POST /auth/send-otp
        - 6-digit OTP boxes (individual inputs, auto-advance on digit entry)
        - 60s countdown for resend
        - "Verify & Login" → POST /auth/verify-otp
      → Google Sign-In button
      → Error: invalid OTP → ngx-toastr error
      → Success: check role → admin/super_admin → /dashboard, else → "Access Denied" message
      → Use Reactive Form with Validators

---

## PHASE D — DASHBOARD

- [x] D-01: Create features/dashboard/dashboard.component.ts — 29 Jun 2026
      
      SECTION 1 — KPI CARDS (row of 4, then row of 4 = 8 total):
      Row 1: Total Users (gradient-primary) | Total Parlors (gradient-success) |
             Active Tournaments (gradient-warning) | Today's Bookings (gradient-danger)
      Row 2: New Users Today | Pending Verification | Total Posts | Total Revenue
      → Data from GET /admin/stats
      → StatsCard component for each card

      SECTION 2 — PERIOD SELECTOR:
      → Buttons: 7 Days | 30 Days | 90 Days
      → Changes all charts below

      SECTION 3 — CHARTS ROW (2 across):
      Left: User Growth (ng2-charts LineChart / AreaChart, 30 days daily users)
      Right: Daily Bookings (ng2-charts BarChart)
      → Data from GET /admin/analytics?period=30d

      SECTION 4 — CHARTS ROW (2 across):
      Left: Game Type Distribution (ng2-charts DoughnutChart with legend)
      Right: Top Parlors by Bookings (ng2-charts HorizontalBarChart)

      SECTION 5 — RECENT ACTIVITY (2 across):
      Left: Recent Registrations (last 5 users — ngx-datatable mini table)
      Right: Pending Verification Queue (parlors waiting — with inline Verify button)

      SECTION 6 — ALERTS:
      → Amber alert box if pending_verification > 0

- [x] D-02: Configure ng2-charts in dashboard — 29 Jun 2026
      → Import BaseChartDirective in component
      → ChartConfiguration for each chart type
      → Dynamic data updates when period changes
      → Responsive charts (fill container width)

---

## PHASE E — USER MANAGEMENT

- [x] E-01: Create features/users/users-list.component.ts — 29 Jun 2026
      
      FILTERS BAR:
      → Search input (debounceTime 300ms → API call)
      → Role dropdown: All | User | Parlor Owner | Admin | Super Admin
      → Status dropdown: All | Active | Banned
      → Results count badge

      NGX-DATATABLE:
      Columns:
      - User (avatar circle + name + parlor name if owner)
      - Contact (phone + email)
      - Role (colored badge — purple=owner, indigo=admin, red=superadmin, grey=user)
      - Status (StatusBadge component — green=active, red=banned)
      - Joined Date (DateFormat pipe)
      - Actions (dropdown menu: View | Ban/Unban | Change Role | Delete)
      
      TABLE CONFIG:
      → columnMode: ColumnMode.force
      → rowHeight: 56
      → headerHeight: 48
      → footerHeight: 56
      → externalPaging: true (server-side)
      → page size selector: 10 | 20 | 50
      → Sort by column header click
      
      ACTIONS (permission-guarded):
      → Ban: SweetAlert2 confirm → PATCH /admin/users/:id {is_active:false}
      → Unban: direct → PATCH /admin/users/:id {is_active:true}
      → Change Role: ngx-bootstrap modal with role selector
      → Delete: SweetAlert2 confirm (danger) → DELETE /admin/users/:id
      → After action: refresh table + toastr success/error

- [x] E-02: Create features/users/user-detail.component.ts — 29 Jun 2026
      → Route: /users/:id
      → User info card: avatar, name, phone, email, role badge, status badge, joined
      → Stats row: Bookings count | Posts liked | Following count | Reviews written
      → Recent bookings mini table (last 5)
      → Recent liked posts (last 5)
      → Action buttons: Edit Role | Ban/Unban | Delete

---

## PHASE F — PARLOR MANAGEMENT

- [x] F-01: Create features/parlors/parlors-list.component.ts — 30 Jun 2026
      
      FILTERS: search | verified status filter
      
      NGX-DATATABLE COLUMNS:
      → Parlor (logo thumbnail 32px + name + address preview)
      → Owner (name + phone)
      → Games (bootstrap chips — first 3, "+N more" if many)
      → Rating (star icons ⭐ + avg + count)
      → Followers (formatted number)
      → Status (Verified ✓ green | Pending amber badge)
      → Actions: Verify | Unverify | View Detail | Delete

      HIGHLIGHT: unverified rows with amber left border-left: 3px solid #ff9f43

- [x] F-02: Create features/parlors/parlor-detail.component.ts — 30 Jun 2026
      → Full parlor card: logo, cover, name, address, hours, game types
      → Tabs (Bootstrap tabs): Overview | Games | Time Slots | Events | Gallery | Reviews
      → Action bar: Verify/Unverify | Edit | Delete

---

## PHASE G — POST MANAGEMENT (text + images + videos + reels)

- [x] G-01: Create features/posts/posts-list.component.ts — 30 Jun 2026
      
      TABS (Bootstrap tabs):
      Tab 1: All Posts
      Tab 2: Images
      Tab 3: Videos
      Tab 4: Reels
      
      FILTERS: search content | media_type filter | date range
      
      NGX-DATATABLE COLUMNS:
      → Parlor (name + logo)
      → Content (truncated 80 chars + expand button)
      → Media Type (badge: text=grey, image=cyan, video=purple, reel=pink)
      → Media (thumbnail if image/video; play icon if video/reel)
      → Geo (📍 icon if has geo_lat/geo_lng — click to see on map)
      → Likes (❤️ count)
      → Comments (💬 count)
      → Date (DateFormat pipe)
      → Actions: View | Delete

      MEDIA PREVIEW (click row):
      → ngx-bootstrap modal with full post content
      → Image gallery (if media_type = image)
      → Video player (HTML5 video if media_type = video/reel)
      → Post details: parlor, content, likes, comments, geo location map

- [x] G-02: Create features/posts/reels-list.component.ts — 30 Jun 2026
      → Filter: media_type=reel only
      → CARD VIEW (not table) — 3 column grid of reel cards
      → Each card: video thumbnail + play button overlay + parlor name + likes + delete button
      → Click card → modal with inline video player

- [x] G-03: Create features/posts/media-viewer.component.ts (shared modal) — 30 Jun 2026
      → ngx-bootstrap BsModalService
      → Input: post object
      → Template: image carousel (Bootstrap) OR html5 video player
      → Show: post text, parlor, date, likes, comments, geo coords
      → If geo: small OpenLayers/Leaflet map preview of location

---

## PHASE H — SOCIAL MANAGEMENT

- [x] H-01: Create features/social/likes-list.component.ts — 30 Jun 2026
      
      HEADER STATS: Total likes today | Total this week | Most liked post
      
      NGX-DATATABLE COLUMNS:
      → User (avatar + name)
      → Target Type (badge: post=blue, comment=grey)
      → Target Preview (post content truncated OR comment text)
      → Parlor (from post)
      → Date & Time
      → Action: Remove Like (soft delete)

- [x] H-02: Create features/social/comments-list.component.ts — 30 Jun 2026
      
      FILTERS: show_deleted toggle | search text
      
      NGX-DATATABLE COLUMNS:
      → User (avatar + name)
      → Comment Text (full text, highlight if deleted with strikethrough)
      → Post (parlor name + post preview)
      → Likes (count)
      → Replies (count)
      → Status (badge: active=green, deleted=red)
      → Date
      → Actions: Remove/Restore | View in context

---

## PHASE I — GEO ACTIVITY

- [x] I-01: Create features/geo/geo-map.component.ts — 30 Jun 2026
      
      PAGE LAYOUT:
      → Left: table of geo-tagged posts/check-ins
      → Right: map showing all geo points
      
      MAP:
      → Use Leaflet.js (add to package.json: leaflet + @types/leaflet)
      → OR use Google Maps (if API key available)
      → Show markers for each geo-tagged post
      → Marker popup: user name, post preview, date
      → Cluster markers when zoomed out (leaflet.markercluster)
      
      TABLE:
      → User | Location (lat/lng formatted) | Post Preview | Date
      → Click row → center map on that location + open popup

---

## PHASE J — TOURNAMENT & BOOKING MANAGEMENT

- [x] J-01: Create features/tournaments/tournaments-list.component.ts — 30 Jun 2026
      FILTERS: search | status filter (open/full/live/completed/cancelled)
      COLUMNS: Title | Parlor | Game Type | Slots (X/Y progress bar) | Entry Fee | Date | Status | Actions
      SLOT PROGRESS BAR: Bootstrap progress bar showing booked/total ratio
      ACTIONS: Change Status (dropdown) | View Bookings | Delete

- [x] J-02: Create features/bookings/bookings-list.component.ts — 30 Jun 2026
      TABS: Tournament Bookings | Time Slot Bookings
      TOURNAMENT TAB COLUMNS: User | Tournament | Parlor | Slot# | Status | Payment | Date
      SLOT TAB COLUMNS: User | Game | Parlor | Date+Time | Price | Status | Date Booked
      FILTER: date range picker | status filter

---

## PHASE K — EVENTS & COMMUNITY

- [x] K-01: Create features/events/events-list.component.ts — 30 Jun 2026
      COLUMNS: Cover thumbnail | Title | Parlor | Type badge | Date | Participants (X/Y) | Entry Fee | Status | Actions
      ACTIONS: Change Status | View Participants (modal) | Delete

- [x] K-02: Create features/community/community-list.component.ts — 30 Jun 2026
      COLUMNS: Author | Title | Tag chip | Views | Likes | Comments | Pinned (toggle) | Date | Actions
      PIN TOGGLE: Bootstrap switch → PATCH /admin/community/:id/pin

---

## PHASE L — ANALYTICS PAGE

- [x] L-01: Create features/analytics/analytics.component.ts — 30 Jun 2026
      
      PERIOD SELECTOR: 7d | 30d | 90d (Bootstrap button group)
      
      KPI ROW: Total Users | New This Period | Total Bookings | Revenue
      
      CHART GRID (ng2-charts):
      Full width: User Growth (AreaChart/LineChart with gradient fill)
      Full width: Bookings Per Day (BarChart)
      Half+Half: Posts Per Day (LineChart) | Game Distribution (PieChart/Doughnut)
      Full width: Top Parlors Table (ngx-datatable + inline mini bar chart per row)
      
      EXPORT: "Export CSV" button → generate and download CSV from table data
      
      CHART STYLING:
      → All charts: white background cards with shadow
      → Line chart: filled area with gradient (primary color 20% opacity)
      → Bar chart: gradient bars (primary color)
      → Pie/Doughnut: custom color array

---

## PHASE M — BROADCAST NOTIFICATIONS

- [x] M-01: Create features/notifications/broadcast.component.ts — 30 Jun 2026
      
      TWO TABS: "Send Broadcast" | "History"
      
      SEND TAB:
      → Target audience: 3 Bootstrap cards (click to select)
        - Everyone (globe icon, indigo)
        - Gamers Only (users icon, green)
        - Parlor Owners (shop icon, purple)
      → Notification type: info | alert | promo | event (Bootstrap pills)
      → Form (Reactive Form):
        - Title input (max 80 chars + counter)
        - Message textarea (max 500 chars + counter)
      → PHONE PREVIEW: Bootstrap phone mockup showing notification preview
        - Dark phone frame with notification card
        - Live preview updates as user types
      → Send button with spinner → POST /admin/notifications/broadcast
      → Success: toastr + "Sent to X users" banner
      
      HISTORY TAB:
      → ngx-datatable: Type | Title | Message (truncated) | Target | Sent To | Date | Status

---

## PHASE N — ROLES & PERMISSIONS

- [x] N-01: Create features/roles/roles.component.ts (super_admin only) — 30 Jun 2026
      
      LAYOUT: Left panel (role selector) + Right panel (permission matrix)
      
      LEFT PANEL:
      → 4 role cards (super_admin, admin, parlor_owner, user)
      → Each card: icon + role name + description + permission count
      → Active border: purple when selected
      → Permission fill bar showing coverage %
      
      RIGHT PANEL — PERMISSION MATRIX:
      → Header: selected role name + permission count + "Save Changes" button
      → Groups: Users | Parlors | Content | Tournaments | Analytics | System
      → Each row: Bootstrap switch toggle + permission name + description
      → super_admin: all locked ON (not editable)
      → admin: editable by super_admin only
      
      COMPARISON TABLE (below):
      → HTML table: Permission | super_admin | admin | parlor_owner | user
      → ✓ = green check, ✕ = grey cross

---

## PHASE O — SETTINGS

- [x] O-01: Create features/settings/settings.component.ts (super_admin only) — 30 Jun 2026
      
      BOOTSTRAP TABS:
      Tab 1 — General: App name, emails, timezone, maintenance mode toggle
      Tab 2 — Feature Flags: Bootstrap switches for: new parlor registration,
               paid tournaments, messaging, community, push notifications
      Tab 3 — Integrations: Twilio, Firebase, Razorpay, AWS S3 status cards
               (green dot = connected, red dot = disconnected, masked keys)
      Tab 4 — Security: JWT expiry settings, rate limiting config, IP whitelist

---

## PHASE P — POLISH & RESPONSIVE

- [x] P-01: Mobile responsive sidebar (collapse to icon-only on < 768px, drawer overlay on < 576px) — 30 Jun 2026
- [x] P-02: Loading states: NgxSpinner on all API calls, skeleton rows in ngx-datatable — 30 Jun 2026
- [x] P-03: Error states: retry button on all failed API calls — 30 Jun 2026
- [x] P-04: Empty states: illustration + message on all empty tables — 30 Jun 2026
- [x] P-05: 404 page + 403 Unauthorized page — 30 Jun 2026
- [x] P-06: Print CSS for analytics reports — 30 Jun 2026
- [x] P-07: Dark/Light mode toggle (add .dark class to body + CSS variables) — 30 Jun 2026
- [x] P-08: ng build --configuration=production → fix any build errors — 30 Jun 2026

---

## SESSION LOG
| Date | Tasks Completed | Next Task | Notes |
|------|----------------|-----------|-------|
| Day 0 | Planning | A-01 | Starting fresh |
| 29 Jun 2026 | A-01 → A-15 (Phase A complete) | B-01 | Core setup, routes, login stub, build passes |
| 29 Jun 2026 | B-01 → B-07 (Phase B complete) | C-01 | Sidebar, topbar, shared UI components |
| 29 Jun 2026 | C-01 (Phase C complete) | D-01 | Full Valex login: OTP + password tabs |
| 29 Jun 2026 | D-01 → D-02 (Phase D complete) | E-01 | Dashboard: KPIs, charts, datatables, mock fallback |
| 29 Jun 2026 | E-01 (Phase E started) | E-02 | Users list: filters, ngx-datatable, ban/role/delete actions |
| 29 Jun 2026 | E-02 (Phase E complete) | F-01 | User detail: profile, stats, bookings/likes tables, actions |
| 30 Jun 2026 | F-01 (Phase F started) | F-02 | Parlors list: filters, ngx-datatable, verify/delete, amber highlight |
| 30 Jun 2026 | F-02 → P-08 (ALL PHASES COMPLETE) | — | Full admin panel: all features + polish, production build passes |
