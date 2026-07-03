import { Link, useLocation } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';

const ROUTE_LABELS: Record<string, string> = {
  dashboard: 'Dashboard', users: 'Users', parlors: 'Parlors', tournaments: 'Tournaments',
  bookings: 'Bookings', posts: 'Posts', comments: 'Comments', events: 'Events',
  community: 'Community', analytics: 'Analytics', roles: 'Roles', notifications: 'Broadcast',
  settings: 'Settings', ratings: 'Ratings', owner: 'My Parlor',
};

interface Props {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  onExport?: () => void;
}

export default function PageHeader({ title, subtitle, actions, onExport }: Props) {
  const { pathname } = useLocation();
  const segments = pathname.split('/').filter(Boolean);
  const crumbs = segments.map((seg, i) => ({
    label: ROUTE_LABELS[seg] ?? (seg.length > 20 ? 'Detail' : seg),
    path: '/' + segments.slice(0, i + 1).join('/'),
  }));

  const pageTitle = title ?? crumbs[crumbs.length - 1]?.label ?? 'Admin';

  return (
    <div className="mb-5 sm:mb-6">
      <nav className="flex items-center gap-1 text-xs text-slate-400 mb-2 flex-wrap" aria-label="Breadcrumb">
        <Link to="/dashboard" className="hover:text-indigo-600 transition-colors">Home</Link>
        {crumbs.map((c, i) => (
          <span key={c.path} className="flex items-center gap-1">
            <ChevronRight size={12} aria-hidden />
            {i < crumbs.length - 1 ? (
              <Link to={c.path} className="hover:text-indigo-600 transition-colors">{c.label}</Link>
            ) : (
              <span className="text-slate-600 font-medium">{c.label}</span>
            )}
          </span>
        ))}
      </nav>
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-xl font-semibold tracking-tight text-slate-900">{pageTitle}</h2>
          {subtitle && <p className="gc-section-subtitle text-slate-500">{subtitle}</p>}
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {onExport && (
            <Button variant="outline" size="sm" onClick={onExport}>Export</Button>
          )}
          {actions}
        </div>
      </div>
    </div>
  );
}