import { cn } from '@/lib/utils';

export default function FilterBar({ children, className, footer }: {
  children: React.ReactNode;
  className?: string;
  footer?: React.ReactNode;
}) {
  return (
    <div className={cn('gc-card-flat overflow-hidden', className)}>
      <div className="flex flex-wrap items-center gap-3 p-4">
        {children}
      </div>
      {footer && <div className="px-4 pb-4 pt-0 border-t border-slate-100">{footer}</div>}
    </div>
  );
}