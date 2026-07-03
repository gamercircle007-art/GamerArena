import { cn } from '@/lib/utils';
import { CHART } from '@/lib/chart-theme';

interface Item {
  id: string;
  label: string;
  value: number;
  suffix?: string;
}

interface Props {
  items: Item[];
  emptyMessage?: string;
  className?: string;
}

export default function RankList({ items, emptyMessage = 'No data yet', className }: Props) {
  const max = Math.max(...items.map(i => i.value), 1);

  return (
    <div className={cn('space-y-3.5 py-1', className)}>
      {items.map((item, i) => (
        <div key={item.id}>
          <div className="flex justify-between text-xs mb-1.5">
            <span className="text-slate-700 font-medium truncate pr-2">
              <span className="text-slate-400 font-normal mr-1.5">{i + 1}.</span>
              {item.label}
            </span>
            <span className="text-slate-500 shrink-0 tabular-nums">
              {item.value}{item.suffix ? ` ${item.suffix}` : ''}
            </span>
          </div>
          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500 ease-out"
              style={{
                width: `${(item.value / max) * 100}%`,
                background: `linear-gradient(90deg, ${CHART.primary}, ${CHART.violet})`,
              }}
            />
          </div>
        </div>
      ))}
      {!items.length && (
        <p className="text-center text-slate-400 text-sm py-8">{emptyMessage}</p>
      )}
    </div>
  );
}