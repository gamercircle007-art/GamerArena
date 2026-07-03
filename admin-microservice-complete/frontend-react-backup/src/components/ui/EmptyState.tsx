import { Inbox } from 'lucide-react';

export default function EmptyState({ message = 'No data found', icon: Icon = Inbox }: {
  message?: string;
  icon?: React.ElementType;
}) {
  return (
    <tr>
      <td colSpan={99}>
        <div className="gc-empty py-20">
          <div className="size-14 rounded-2xl bg-slate-50 flex items-center justify-center mb-3 ring-1 ring-slate-100">
            <Icon className="size-6 text-slate-300" aria-hidden />
          </div>
          <p className="text-sm font-medium text-slate-500">{message}</p>
          <p className="text-xs text-slate-400 mt-1">Data will appear here once available</p>
        </div>
      </td>
    </tr>
  );
}