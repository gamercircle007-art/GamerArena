import ErrorBanner from './ErrorBanner';
import Pagination from './Pagination';
import { cn } from '@/lib/utils';

interface Props {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  toolbar?: React.ReactNode;
  isError?: boolean;
  onRetry?: () => void;
  errorMessage?: string;
  page?: number;
  pages?: number;
  total?: number;
  onPageChange?: (page: number) => void;
  pageSize?: number;
  className?: string;
  compact?: boolean;
  bare?: boolean;
}

export default function AdminTable({
  children, title, subtitle, toolbar,
  isError, onRetry, errorMessage,
  page, pages = 1, total = 0, onPageChange, pageSize = 10,
  className, compact, bare,
}: Props) {
  const content = (
    <>
      {(title || toolbar) && (
        <div className={cn('gc-card-header flex flex-col sm:flex-row sm:items-center justify-between gap-3', compact && 'py-3')}>
          {(title || subtitle) && (
            <div>
              {title && <h3 className="gc-section-title">{title}</h3>}
              {subtitle && <p className="gc-section-subtitle">{subtitle}</p>}
            </div>
          )}
          {toolbar}
        </div>
      )}
      {isError && <ErrorBanner message={errorMessage} onRetry={onRetry} />}
      <div className="overflow-x-auto">
        <table className="gc-table w-full">{children}</table>
      </div>
      {onPageChange && page !== undefined && (
        <Pagination page={page} pages={pages} total={total} onPageChange={onPageChange} pageSize={pageSize} />
      )}
    </>
  );

  if (bare) {
    return <div className={cn('overflow-hidden', className)}>{content}</div>;
  }

  return (
    <div className={cn('gc-card-flat overflow-hidden', className)}>
      {content}
    </div>
  );
}