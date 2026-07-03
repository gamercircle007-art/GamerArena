import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import ScrollToTop from './components/ScrollToTop';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from '@/components/ui/sonner';
import { Button } from '@/components/ui/button';
import { useAuthStore } from './context/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import AdminLayout from './layouts/AdminLayout';
import OwnerLayout from './pages/owner/OwnerLayout';

const LoginPage         = lazy(() => import('./pages/auth/LoginPage'));
const DashboardPage     = lazy(() => import('./pages/dashboard/DashboardPage'));
const UsersPage         = lazy(() => import('./pages/users/UsersPage'));
const UserDetailPage    = lazy(() => import('./pages/users/UserDetailPage'));
const ParlorsPage       = lazy(() => import('./pages/parlors/ParlorsPage'));
const ParlorDetailPage  = lazy(() => import('./pages/parlors/ParlorDetailPage'));
const TournamentsPage   = lazy(() => import('./pages/tournaments/TournamentsPage'));
const BookingsPage      = lazy(() => import('./pages/bookings/BookingsPage'));
const PostsPage         = lazy(() => import('./pages/posts/PostsPage'));
const CommentsPage      = lazy(() => import('./pages/comments/CommentsPage'));
const EventsPage        = lazy(() => import('./pages/events/EventsPage'));
const CommunityPage     = lazy(() => import('./pages/community/CommunityPage'));
const RatingsPage       = lazy(() => import('./pages/ratings/RatingsPage'));
const AnalyticsPage     = lazy(() => import('./pages/analytics/AnalyticsPage'));
const RolesPage         = lazy(() => import('./pages/roles/RolesPage'));
const NotificationsPage = lazy(() => import('./pages/notifications/NotificationsPage'));
const SettingsPage      = lazy(() => import('./pages/settings/SettingsPage'));
const OwnerDashboardPage = lazy(() => import('./pages/owner/OwnerDashboardPage'));
const NotFoundPage      = lazy(() => import('./pages/NotFoundPage'));

const qc = new QueryClient({ defaultOptions: { queries: { staleTime: 30_000, retry: 1 } } });

function RequireAuth() {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Outlet />;
}

function RequireAdmin() {
  const { user } = useAuthStore();
  if (user?.role === 'parlor_owner') return <Navigate to="/owner" replace />;
  if (user?.role !== 'super_admin' && user?.role !== 'admin') return <Navigate to="/unauthorized" replace />;
  return <Outlet />;
}

function RequireOwner() {
  const { user } = useAuthStore();
  if (user?.role !== 'parlor_owner') return <Navigate to="/dashboard" replace />;
  return <Outlet />;
}

const Spin = () => (
  <div className="flex items-center justify-center h-svh bg-muted/30">
    <div className="size-8 animate-spin rounded-full border-2 border-primary border-t-transparent" role="status" aria-label="Loading" />
  </div>
);

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <Toaster position="top-right" richColors closeButton />
      <BrowserRouter>
        <ScrollToTop />
        <ErrorBoundary>
          <Suspense fallback={<Spin />}>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/unauthorized" element={<Unauthorized />} />

              <Route element={<RequireAuth />}>
                <Route element={<RequireOwner />}>
                  <Route element={<OwnerLayout />}>
                    <Route path="/owner" element={<OwnerDashboardPage />} />
                  </Route>
                </Route>

                <Route element={<RequireAdmin />}>
                  <Route element={<AdminLayout />}>
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                    <Route path="/dashboard"      element={<DashboardPage />} />
                    <Route path="/users"          element={<UsersPage />} />
                    <Route path="/users/:id"      element={<UserDetailPage />} />
                    <Route path="/parlors"        element={<ParlorsPage />} />
                    <Route path="/parlors/:id"    element={<ParlorDetailPage />} />
                    <Route path="/tournaments"    element={<TournamentsPage />} />
                    <Route path="/bookings"       element={<BookingsPage />} />
                    <Route path="/posts"          element={<PostsPage />} />
                    <Route path="/comments"       element={<CommentsPage />} />
                    <Route path="/events"         element={<EventsPage />} />
                    <Route path="/community"      element={<CommunityPage />} />
                    <Route path="/ratings"        element={<RatingsPage />} />
                    <Route path="/analytics"      element={<AnalyticsPage />} />
                    <Route path="/roles"          element={<RolesPage />} />
                    <Route path="/notifications"  element={<NotificationsPage />} />
                    <Route path="/settings"       element={<SettingsPage />} />
                    <Route path="*"               element={<NotFoundPage />} />
                  </Route>
                </Route>
              </Route>
            </Routes>
          </Suspense>
        </ErrorBoundary>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

function Unauthorized() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-4 bg-muted/30 p-6">
      <div className="text-6xl" aria-hidden>🚫</div>
      <h1 className="text-2xl font-bold">Access Denied</h1>
      <p className="text-muted-foreground text-center max-w-sm">You don't have permission to access the admin panel.</p>
      <Button asChild>
        <a href="/login">Go to Login</a>
      </Button>
    </div>
  );
}