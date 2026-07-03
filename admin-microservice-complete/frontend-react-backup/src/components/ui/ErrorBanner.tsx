import { AlertCircle } from 'lucide-react';
import Button from '@/components/app/Button';

export default function ErrorBanner({ message = 'Failed to load data', onRetry }: {
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="gc-alert-error" role="alert">
      <span className="flex items-center gap-2">
        <AlertCircle size={16} aria-hidden />
        {message}
      </span>
      {onRetry && (
        <Button variant="ghost" size="sm" onClick={onRetry}>Retry</Button>
      )}
    </div>
  );
}