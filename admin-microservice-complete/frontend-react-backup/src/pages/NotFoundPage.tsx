import { Link } from 'react-router-dom';
import { Home, ArrowLeft } from 'lucide-react';
import { PageShell, Button } from '../components/ui';

export default function NotFoundPage() {
  return (
    <PageShell>
      <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 py-12">
        <div className="text-7xl font-bold text-slate-200">404</div>
        <h1 className="gc-page-title text-center">Page not found</h1>
        <p className="gc-section-subtitle text-center max-w-sm">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="flex gap-3 mt-2">
          <Button variant="secondary" onClick={() => window.history.back()}>
            <ArrowLeft size={14} /> Go Back
          </Button>
          <Link to="/dashboard">
            <Button variant="primary">
              <Home size={14} /> Dashboard
            </Button>
          </Link>
        </div>
      </div>
    </PageShell>
  );
}