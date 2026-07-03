import { TrendingUp, TrendingDown } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { CardSkeleton } from '../app/Skeleton';
import { cn } from '@/lib/utils';

interface Props {
  title: string;
  value: string | number;
  Icon: LucideIcon;
  color?: keyof typeof colorMap;
  trend?: number;
  subtitle?: string;
  loading?: boolean;
}

const colorMap = {
  indigo: { bg: 'bg-indigo-50', text: 'text-indigo-600', ring: 'ring-indigo-100' },
  violet: { bg: 'bg-violet-50', text: 'text-violet-600', ring: 'ring-violet-100' },
  green:  { bg: 'bg-emerald-50', text: 'text-emerald-600', ring: 'ring-emerald-100' },
  amber:  { bg: 'bg-amber-50', text: 'text-amber-600', ring: 'ring-amber-100' },
  red:    { bg: 'bg-red-50', text: 'text-red-600', ring: 'ring-red-100' },
  cyan:   { bg: 'bg-cyan-50', text: 'text-cyan-600', ring: 'ring-cyan-100' },
  pink:   { bg: 'bg-pink-50', text: 'text-pink-600', ring: 'ring-pink-100' },
  slate:  { bg: 'bg-slate-50', text: 'text-slate-600', ring: 'ring-slate-100' },
} as const;

export default function StatCard({ title, value, Icon, color = 'indigo', trend, subtitle, loading }: Props) {
  if (loading) return <div className="gc-card-flat p-5 min-h-[8.5rem]"><CardSkeleton className="!h-full" /></div>;

  const palette = colorMap[color] ?? colorMap.indigo;

  return (
    <div className="gc-card group p-4 sm:p-5">
      <div className="flex items-start justify-between mb-3">
        <div className={cn(
          'size-10 rounded-xl flex items-center justify-center ring-1 transition-transform group-hover:scale-105',
          palette.bg, palette.text, palette.ring,
        )}>
          <Icon size={18} aria-hidden />
        </div>
        {trend !== undefined && (
          <span className={cn(
            'flex items-center gap-0.5 text-xs font-semibold px-2 py-0.5 rounded-lg',
            trend >= 0 ? 'text-emerald-700 bg-emerald-50' : 'text-red-600 bg-red-50',
          )}>
            {trend >= 0 ? <TrendingUp size={12} aria-hidden /> : <TrendingDown size={12} aria-hidden />}
            {Math.abs(trend)}%
          </span>
        )}
      </div>
      <div className="text-2xl sm:text-[1.65rem] font-bold tracking-tight text-slate-900 tabular-nums leading-none mb-1.5">
        {value}
      </div>
      <div className="text-sm font-medium text-slate-600">{title}</div>
      {subtitle && <div className="text-xs text-slate-400 mt-1">{subtitle}</div>}
    </div>
  );
}