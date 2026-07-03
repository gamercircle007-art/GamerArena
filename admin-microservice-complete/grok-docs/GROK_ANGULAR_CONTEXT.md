# GROK — ANGULAR 21 ADMIN PANEL CONTEXT
# Paste this after STEP1_SCAN_BACKEND.md is done.
# Reference: API_REFERENCE.md (from Step 1 scan) + this file.
# ─────────────────────────────────────────────────────────────────────────────

You are building a **production Angular 21 admin panel** for the GameConnect platform.
Design reference: Valex-style — colored sidebar, gradient stat cards, charts, data tables.
Backend: Python FastAPI running at http://localhost:8000/v1

## SCAN EXISTING PROJECT FIRST
```bash
ls -la                                      # project root
ls src/app/ 2>/dev/null                    # existing Angular structure
cat package.json 2>/dev/null               # installed packages
cat src/app/app.routes.ts 2>/dev/null      # existing routes
cat API_REFERENCE.md 2>/dev/null           # backend API scan
cat PROGRESS_ANGULAR.md                    # current build status
```

---

## TECH STACK (exact versions)
| Package | Version | Purpose |
|---------|---------|---------|
| @angular/core | ^21.0.0 | Framework |
| bootstrap | ^5.3.3 | CSS framework |
| ngx-bootstrap | ^18.0.0 | Angular Bootstrap components |
| @swimlane/ngx-datatable | ^20.0.0 | Smart data tables |
| ng2-charts | ^6.0.0 | Chart.js wrapper |
| chart.js | ^4.4.0 | Charts |
| ngx-toastr | ^19.0.0 | Toast notifications |
| sweetalert2 | ^11.14.0 | Confirm dialogs |
| @ng-icons/core | ^29.4.0 | Icons |
| @ng-icons/bootstrap-icons | ^29.4.0 | Bootstrap icons |
| ngx-spinner | ^17.0.0 | Loading spinner |
| @angular/animations | ^21.0.0 | Sidebar animations |

## INSTALL COMMAND
```bash
npm install bootstrap ngx-bootstrap @swimlane/ngx-datatable ng2-charts chart.js \
  ngx-toastr sweetalert2 @ng-icons/core @ng-icons/bootstrap-icons ngx-spinner
```

---

## ANGULAR 21 PATTERNS (always use these — never old NgModule pattern)

### Standalone components (always)
```typescript
@Component({
  standalone: true,
  imports: [CommonModule, RouterOutlet, FormsModule, ReactiveFormsModule, ...],
  template: `...`,
})
export class MyComponent {
  private service = inject(MyService);  // use inject(), not constructor
  count = signal(0);                    // signals for reactive state
  doubled = computed(() => this.count() * 2);
}
```

### New template control flow
```html
@if (isLoading()) {
  <div class="spinner"></div>
} @else {
  <div>Content</div>
}

@for (item of items(); track item.id) {
  <tr>{{ item.name }}</tr>
} @empty {
  <tr>No data</tr>
}

@switch (user.role) {
  @case ('admin') { <admin-badge /> }
  @case ('super_admin') { <superadmin-badge /> }
  @default { <user-badge /> }
}
```

### Input/Output signals
```typescript
// New API
title = input<string>('');
onSave = output<void>();

// Usage in template
<my-comp [title]="'Hello'" (onSave)="handleSave()" />
```

### HttpClient with signals
```typescript
private http = inject(HttpClient);
users = signal<User[]>([]);

loadUsers() {
  this.http.get<PaginatedResponse<User>>('/admin/users')
    .pipe(takeUntilDestroyed())
    .subscribe(data => this.users.set(data.items));
}
```

### app.config.ts (not app.module.ts)
```typescript
export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withInterceptors([authInterceptor, loadingInterceptor])),
    provideAnimations(),
    importProvidersFrom(
      NgxBootstrapModule,
      ToastrModule.forRoot(),
      NgxSpinnerModule,
    ),
  ],
};
```

---

## PROJECT STRUCTURE
```
src/
├── app/
│   ├── core/
│   │   ├── guards/
│   │   │   ├── auth.guard.ts          # canActivate → redirect to /login
│   │   │   └── role.guard.ts          # canActivate → check role permission
│   │   ├── interceptors/
│   │   │   ├── auth.interceptor.ts    # attach Bearer token to every request
│   │   │   └── loading.interceptor.ts # show/hide NgxSpinner
│   │   ├── services/
│   │   │   ├── auth.service.ts        # login, logout, token management
│   │   │   ├── admin-api.service.ts   # all /admin/* API calls
│   │   │   └── toast.service.ts       # toastr wrapper
│   │   ├── models/
│   │   │   └── index.ts               # all TypeScript interfaces
│   │   └── constants/
│   │       └── permissions.ts         # RBAC roles + permissions
│   ├── shared/
│   │   ├── components/
│   │   │   ├── sidebar/               # collapsible left sidebar
│   │   │   ├── topbar/                # top navigation bar
│   │   │   ├── stats-card/            # colored KPI card
│   │   │   ├── confirm-modal/         # SweetAlert2 wrapper service
│   │   │   ├── status-badge/          # colored status pill
│   │   │   └── page-header/           # title + breadcrumb + actions
│   │   └── pipes/
│   │       ├── date-format.pipe.ts
│   │       ├── currency-in.pipe.ts
│   │       └── truncate.pipe.ts
│   ├── layout/
│   │   └── admin-layout/
│   │       └── admin-layout.component.ts  # sidebar + topbar + router-outlet
│   ├── features/
│   │   ├── auth/
│   │   │   └── login/login.component.ts
│   │   ├── dashboard/
│   │   │   └── dashboard.component.ts
│   │   ├── users/
│   │   │   ├── users-list.component.ts
│   │   │   └── user-detail.component.ts
│   │   ├── parlors/
│   │   │   ├── parlors-list.component.ts
│   │   │   └── parlor-detail.component.ts
│   │   ├── posts/
│   │   │   ├── posts-list.component.ts      # text posts
│   │   │   ├── reels-list.component.ts      # video reels
│   │   │   └── media-viewer.component.ts    # images/videos
│   │   ├── social/
│   │   │   ├── likes-list.component.ts
│   │   │   └── comments-list.component.ts
│   │   ├── tournaments/
│   │   │   └── tournaments-list.component.ts
│   │   ├── bookings/
│   │   │   └── bookings-list.component.ts
│   │   ├── events/
│   │   │   └── events-list.component.ts
│   │   ├── community/
│   │   │   └── community-list.component.ts
│   │   ├── geo/
│   │   │   └── geo-map.component.ts         # user geo location map
│   │   ├── analytics/
│   │   │   └── analytics.component.ts
│   │   ├── roles/
│   │   │   └── roles.component.ts
│   │   ├── notifications/
│   │   │   └── broadcast.component.ts
│   │   └── settings/
│   │       └── settings.component.ts
│   ├── app.component.ts
│   ├── app.config.ts
│   └── app.routes.ts
├── assets/
│   └── images/
├── environments/
│   ├── environment.ts
│   └── environment.prod.ts
└── styles.scss                              # Bootstrap + custom variables
```

---

## DESIGN SYSTEM (Valex-inspired)

### Color Variables (styles.scss)
```scss
// Primary palette
$primary:    #7367f0;   // purple (sidebar, primary buttons)
$secondary:  #82868b;
$success:    #28c76f;
$warning:    #ff9f43;
$danger:     #ea5455;
$info:       #00cfe8;
$dark:       #4b4b4b;

// Sidebar
$sidebar-bg:     #283046;  // dark blue
$sidebar-width:  260px;
$sidebar-collapsed-width: 70px;

// Cards
$card-shadow: 0 4px 24px 0 rgba(34,41,47,.1);
```

### Stat Card Gradients
```
Card 1 (Users):     gradient-primary   → purple to blue
Card 2 (Parlors):   gradient-success   → green to teal
Card 3 (Bookings):  gradient-warning   → orange to yellow
Card 4 (Revenue):   gradient-danger    → red to pink
```

### Sidebar nav item active state
```scss
.nav-link.active {
  background: linear-gradient(118deg, #7367f0, rgba(115,103,240,.7));
  box-shadow: 0 0 10px 1px rgba(115,103,240,.7);
  border-radius: 4px;
  color: #fff !important;
}
```

---

## ALL BACKEND API ENDPOINTS (use API_REFERENCE.md for actual paths)

```typescript
// Base URL from environment
API_BASE = environment.apiUrl  // 'http://localhost:8000/v1'

// AUTH
POST   /auth/send-otp         → {phone}
POST   /auth/verify-otp       → {phone, otp} → {access_token, refresh_token, user}
POST   /auth/google
POST   /auth/refresh
POST   /auth/logout

// ADMIN — STATS
GET    /admin/stats            → AdminStats

// ADMIN — USERS
GET    /admin/users            → ?page&limit&search&role&is_active
GET    /admin/users/:id
PATCH  /admin/users/:id        → {is_active?, role?}
DELETE /admin/users/:id

// ADMIN — PARLORS
GET    /admin/parlors          → ?page&limit&search&is_verified
PATCH  /admin/parlors/:id/verify → {is_verified}
DELETE /admin/parlors/:id

// ADMIN — POSTS (TEXT + IMAGES + REELS + VIDEOS)
GET    /admin/posts            → ?page&limit&search&media_type=image|video|reel
DELETE /admin/posts/:id

// ADMIN — LIKES & COMMENTS (social)
GET    /admin/likes            → ?page&target_type=post|comment
GET    /admin/comments         → ?page&is_deleted
DELETE /admin/comments/:id

// ADMIN — TOURNAMENTS
GET    /admin/tournaments      → ?page&search&status
PATCH  /admin/tournaments/:id/status → {status}
DELETE /admin/tournaments/:id

// ADMIN — BOOKINGS
GET    /admin/bookings         → ?page&type=tournament|slot

// ADMIN — EVENTS
GET    /admin/events           → ?page&status
DELETE /admin/events/:id

// ADMIN — COMMUNITY
GET    /admin/community        → ?page
PATCH  /admin/community/:id/pin → {is_pinned}
DELETE /admin/community/:id

// ADMIN — RATINGS
GET    /admin/ratings          → ?page
DELETE /admin/ratings/:id

// ADMIN — GEO ACTIVITY (if exists in your backend)
GET    /admin/geo-activity     → ?page  (user check-ins / location data)
GET    /geo/nearby-parlors     → ?lat&lng&radius

// ADMIN — ANALYTICS
GET    /admin/analytics        → ?period=7d|30d|90d

// ADMIN — BROADCAST NOTIFICATIONS
POST   /admin/notifications/broadcast → {title, body, target, type}
```

---

## ROLES + PERMISSIONS (RBAC)

```typescript
// core/constants/permissions.ts
export const ROLES = {
  SUPER_ADMIN: 'super_admin',
  ADMIN: 'admin',
  PARLOR_OWNER: 'parlor_owner',
  USER: 'user',
} as const;

export const ROLE_PERMISSIONS = {
  super_admin: ['*'],  // everything
  admin: [
    'view_users', 'ban_users', 'delete_users',
    'view_parlors', 'verify_parlors', 'delete_parlors',
    'view_posts', 'delete_posts', 'moderate_comments',
    'view_tournaments', 'manage_tournaments',
    'view_bookings', 'view_events', 'view_community',
    'view_analytics', 'send_broadcast',
    'view_ratings', 'view_geo',
  ],
  parlor_owner: ['view_own_analytics', 'view_own_bookings'],
  user: [],
};
```

---

## ROUTING (app.routes.ts)
```typescript
export const routes: Routes = [
  { path: 'login', loadComponent: () => import('./features/auth/login/login.component') },
  {
    path: '',
    component: AdminLayoutComponent,
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard',     loadComponent: () => import('./features/dashboard/dashboard.component') },
      { path: 'users',         loadComponent: () => import('./features/users/users-list.component') },
      { path: 'users/:id',     loadComponent: () => import('./features/users/user-detail.component') },
      { path: 'parlors',       loadComponent: () => import('./features/parlors/parlors-list.component') },
      { path: 'posts',         loadComponent: () => import('./features/posts/posts-list.component') },
      { path: 'posts/reels',   loadComponent: () => import('./features/posts/reels-list.component') },
      { path: 'social/likes',  loadComponent: () => import('./features/social/likes-list.component') },
      { path: 'social/comments',loadComponent: () => import('./features/social/comments-list.component') },
      { path: 'tournaments',   loadComponent: () => import('./features/tournaments/tournaments-list.component') },
      { path: 'bookings',      loadComponent: () => import('./features/bookings/bookings-list.component') },
      { path: 'events',        loadComponent: () => import('./features/events/events-list.component') },
      { path: 'community',     loadComponent: () => import('./features/community/community-list.component') },
      { path: 'geo',           loadComponent: () => import('./features/geo/geo-map.component') },
      { path: 'analytics',     loadComponent: () => import('./features/analytics/analytics.component') },
      { path: 'roles',         loadComponent: () => import('./features/roles/roles.component'), canActivate: [roleGuard('super_admin')] },
      { path: 'notifications', loadComponent: () => import('./features/notifications/broadcast.component') },
      { path: 'settings',      loadComponent: () => import('./features/settings/settings.component'), canActivate: [roleGuard('super_admin')] },
    ],
  },
  { path: '**', redirectTo: '' },
];
```

---

## CODING RULES
1. **Always standalone components.** Never NgModule.
2. **inject() pattern.** No constructor injection.
3. **Signals everywhere.** `signal()`, `computed()`, `effect()` over BehaviorSubject.
4. **New template syntax.** `@if`, `@for`, `@switch`. Never `*ngIf`, `*ngFor`.
5. **Typed HTTP.** Every `http.get<Type>()` with proper interface.
6. **Angular animations** for sidebar collapse (smooth 300ms transition).
7. **ngx-datatable** for all data tables (not basic HTML tables).
8. **ng2-charts** for all charts — BarChart, LineChart, PieChart, DoughnutChart.
9. **SweetAlert2** for all confirm dialogs (not browser alert).
10. **ngx-toastr** for all success/error messages.
11. **Reactive Forms** for all forms. Never template-driven.
12. **OnPush change detection** on all components.
13. **takeUntilDestroyed()** in every subscription.
14. **Bootstrap 5 grid** for layout. No custom grid.

---

## SIDEBAR ANIMATION (Angular animations)
```typescript
// In sidebar component
export const sidebarAnimation = trigger('sidebarState', [
  state('expanded', style({ width: '260px' })),
  state('collapsed', style({ width: '70px' })),
  transition('expanded <=> collapsed', animate('300ms ease-in-out')),
]);
```

---

## START: Scan project → read PROGRESS_ANGULAR.md → build next unchecked task.
