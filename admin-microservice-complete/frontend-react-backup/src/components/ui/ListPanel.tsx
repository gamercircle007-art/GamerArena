import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';

interface ListItem {
  id: string;
  title: string;
  subtitle?: string;
  href?: string;
  avatar?: React.ReactNode;
  action?: React.ReactNode;
}

interface Props {
  title: string;
  items: ListItem[];
  emptyMessage?: string;
  className?: string;
}

export default function ListPanel({ title, items, emptyMessage = 'No data yet', className }: Props) {
  return (
    <div className={cn('gc-list-panel', className)}>
      <div className="gc-card-header">
        <h3 className="gc-section-title">{title}</h3>
      </div>
      <div className="divide-y divide-slate-100/80">
        {items.map(item => {
          const row = (
            <div className="flex items-center justify-between gap-3 px-4 sm:px-5 py-3.5 hover:bg-indigo-50/30 transition-colors">
              <div className="flex items-center gap-3 min-w-0 flex-1">
                {item.avatar}
                <div className="min-w-0">
                  <div className="text-sm font-medium text-slate-800 truncate">{item.title}</div>
                  {item.subtitle && <div className="text-xs text-slate-400 truncate">{item.subtitle}</div>}
                </div>
              </div>
              {item.action}
            </div>
          );
          return item.href
            ? <Link key={item.id} to={item.href} className="block">{row}</Link>
            : <div key={item.id}>{row}</div>;
        })}
        {!items.length && (
          <p className="px-5 py-10 text-center text-sm text-slate-400">{emptyMessage}</p>
        )}
      </div>
    </div>
  );
}