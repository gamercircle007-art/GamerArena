import { Badge } from './badge';
import { cn } from '@/lib/utils';

const STYLES: Record<string, string> = {
  active: 'bg-emerald-100 text-emerald-700 hover:bg-emerald-100',
  banned: 'bg-red-100 text-red-700 hover:bg-red-100',
  verified: 'bg-emerald-100 text-emerald-700 hover:bg-emerald-100',
  unverified: 'bg-amber-100 text-amber-700 hover:bg-amber-100',
  open: 'bg-blue-100 text-blue-700 hover:bg-blue-100',
  live: 'bg-violet-100 text-violet-700 hover:bg-violet-100',
  completed: 'bg-slate-100 text-slate-600 hover:bg-slate-100',
  cancelled: 'bg-red-100 text-red-600 hover:bg-red-100',
  pending: 'bg-amber-100 text-amber-700 hover:bg-amber-100',
  confirmed: 'bg-emerald-100 text-emerald-700 hover:bg-emerald-100',
  paid: 'bg-emerald-100 text-emerald-700 hover:bg-emerald-100',
  failed: 'bg-red-100 text-red-700 hover:bg-red-100',
  deleted: 'bg-slate-100 text-slate-500 hover:bg-slate-100',
  sent: 'bg-emerald-100 text-emerald-700 hover:bg-emerald-100',
  draft: 'bg-slate-100 text-slate-500 hover:bg-slate-100',
};

export default function StatusBadge({ status }: { status: string }) {
  const key = status?.toLowerCase().replace(/\s/g, '_') ?? 'unknown';
  return (
    <Badge variant="secondary" className={cn('capitalize font-medium', STYLES[key] ?? 'bg-muted text-muted-foreground')}>
      {status?.replace(/_/g, ' ') ?? '—'}
    </Badge>
  );
}