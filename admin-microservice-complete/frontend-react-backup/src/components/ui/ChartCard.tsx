import { Skeleton } from '../app/Skeleton';
import { cn } from '@/lib/utils';

interface Props {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
}

export function ChartCard({ title, subtitle, children, className }: Props) {
  return (
    <div className={cn('gc-card-flat', className)}>
      <div className="gc-card-header py-4">
        <h3 className="gc-section-title">{title}</h3>
        {subtitle && <p className="gc-section-subtitle">{subtitle}</p>}
      </div>
      <div className="gc-card-body pt-0 pb-5">{children}</div>
    </div>
  );
}

export function ChartSkeleton({ height = 220 }: { height?: number }) {
  return <Skeleton className="w-full rounded-xl bg-slate-100" style={{ height }} />;
}