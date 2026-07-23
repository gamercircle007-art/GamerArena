import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';
import { AdminLayoutComponent } from './layout/admin-layout/admin-layout.component';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () =>
      import('./features/auth/login/login.component').then((m) => m.LoginComponent),
  },
  {
    path: '',
    component: AdminLayoutComponent,
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
      },
      {
        path: 'users',
        loadComponent: () =>
          import('./features/users/users-list.component').then((m) => m.UsersListComponent),
      },
      {
        path: 'users/:id',
        loadComponent: () =>
          import('./features/users/user-detail.component').then((m) => m.UserDetailComponent),
      },
      {
        path: 'parlors',
        loadComponent: () =>
          import('./features/parlors/parlors-list.component').then((m) => m.ParlorsListComponent),
      },
      {
        path: 'parlors/new',
        loadComponent: () =>
          import('./features/parlors/parlor-form.component').then((m) => m.ParlorFormComponent),
      },
      {
        path: 'parlors/:id/edit',
        loadComponent: () =>
          import('./features/parlors/parlor-form.component').then((m) => m.ParlorFormComponent),
      },
      {
        path: 'parlors/:id',
        loadComponent: () =>
          import('./features/parlors/parlor-detail.component').then((m) => m.ParlorDetailComponent),
      },
      {
        path: 'dms',
        loadComponent: () =>
          import('./features/dms/dms-list.component').then((m) => m.DmsListComponent),
      },
      {
        path: 'posts',
        loadComponent: () =>
          import('./features/posts/posts-list.component').then((m) => m.PostsListComponent),
      },
      {
        path: 'posts/reels',
        loadComponent: () =>
          import('./features/posts/reels-list.component').then((m) => m.ReelsListComponent),
      },
      {
        path: 'social/likes',
        loadComponent: () =>
          import('./features/social/likes-list.component').then((m) => m.LikesListComponent),
      },
      {
        path: 'social/comments',
        loadComponent: () =>
          import('./features/social/comments-list.component').then((m) => m.CommentsListComponent),
      },
      {
        path: 'tournaments',
        loadComponent: () =>
          import('./features/tournaments/tournaments-list.component').then(
            (m) => m.TournamentsListComponent,
          ),
      },
      {
        path: 'bookings',
        loadComponent: () =>
          import('./features/bookings/bookings-list.component').then(
            (m) => m.BookingsListComponent,
          ),
      },
      {
        path: 'slots',
        loadComponent: () =>
          import('./features/slots/slots-list.component').then((m) => m.SlotsListComponent),
      },
      {
        path: 'offers',
        loadComponent: () =>
          import('./features/offers/offers-list.component').then((m) => m.OffersListComponent),
      },
      {
        path: 'events',
        loadComponent: () =>
          import('./features/events/events-list.component').then((m) => m.EventsListComponent),
      },
      {
        path: 'community',
        loadComponent: () =>
          import('./features/community/community-list.component').then(
            (m) => m.CommunityListComponent,
          ),
      },
      {
        path: 'geo',
        loadComponent: () =>
          import('./features/geo/geo-map.component').then((m) => m.GeoMapComponent),
      },
      {
        path: 'ratings',
        loadComponent: () =>
          import('./features/ratings/ratings-list.component').then((m) => m.RatingsListComponent),
      },
      {
        path: 'analytics',
        loadComponent: () =>
          import('./features/analytics/analytics.component').then((m) => m.AnalyticsComponent),
      },
      {
        path: 'roles',
        canActivate: [roleGuard('super_admin')],
        loadComponent: () =>
          import('./features/roles/roles.component').then((m) => m.RolesComponent),
      },
      {
        path: 'notifications',
        loadComponent: () =>
          import('./features/notifications/broadcast.component').then(
            (m) => m.BroadcastComponent,
          ),
      },
      {
        path: 'settings',
        canActivate: [roleGuard('super_admin')],
        loadComponent: () =>
          import('./features/settings/settings.component').then((m) => m.SettingsComponent),
      },
      {
        path: 'unauthorized',
        loadComponent: () =>
          import('./features/errors/unauthorized.component').then((m) => m.UnauthorizedComponent),
      },
    ],
  },
  {
    path: '404',
    loadComponent: () =>
      import('./features/errors/not-found.component').then((m) => m.NotFoundComponent),
  },
  { path: '**', loadComponent: () => import('./features/errors/not-found.component').then((m) => m.NotFoundComponent) },
];