import { Link } from 'react-router-dom';
import type { ColumnDef } from '@tanstack/react-table';
import type { ParlorStat, User } from '@/types';
import { formatDate } from '@/utils/formatters';
import { CHART } from '@/lib/chart-theme';

export const topParlorsColumns: ColumnDef<ParlorStat>[] = [
  {
    id: 'rank',
    header: '#',
    cell: ({ row }) => (
      <span className="text-xs font-medium text-slate-400 w-6 inline-block">{row.index + 1}</span>
    ),
    size: 40,
  },
  {
    accessorKey: 'parlor_name',
    header: 'Parlor',
    cell: ({ row }) => (
      <span className="font-medium text-slate-800">{row.original.parlor_name}</span>
    ),
  },
  {
    accessorKey: 'bookings_count',
    header: 'Bookings',
    cell: ({ row }) => (
      <span className="tabular-nums text-slate-600">{row.original.bookings_count.toLocaleString()}</span>
    ),
  },
  {
    accessorKey: 'revenue',
    header: 'Revenue',
    cell: ({ row }) => (
      <span className="tabular-nums text-emerald-600 font-medium">
        ₹{row.original.revenue.toLocaleString()}
      </span>
    ),
  },
  {
    id: 'share',
    header: 'Share',
    cell: ({ row, table }) => {
      const max = Math.max(...table.getRowModel().rows.map(r => r.original.bookings_count), 1);
      const pct = (row.original.bookings_count / max) * 100;
      return (
        <div className="flex items-center gap-2 min-w-[6rem]">
          <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full"
              style={{
                width: `${pct}%`,
                background: `linear-gradient(90deg, ${CHART.primary}, ${CHART.violet})`,
              }}
            />
          </div>
          <span className="text-[10px] text-slate-400 tabular-nums">{Math.round(pct)}%</span>
        </div>
      );
    },
  },
];

export const recentUsersColumns: ColumnDef<User>[] = [
  {
    id: 'user',
    header: 'User',
    cell: ({ row }) => (
      <div className="flex items-center gap-3">
        <div className="size-9 rounded-full bg-gradient-to-br from-indigo-100 to-violet-100 flex items-center justify-center text-indigo-600 text-sm font-bold ring-2 ring-white shrink-0">
          {row.original.name?.[0]?.toUpperCase()}
        </div>
        <div className="min-w-0">
          <div className="font-medium text-slate-800 truncate">{row.original.name}</div>
          <div className="text-xs text-slate-400 truncate">{row.original.email ?? row.original.phone}</div>
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'role',
    header: 'Role',
    cell: ({ row }) => (
      <span className="gc-badge bg-indigo-50 text-indigo-700 capitalize">{row.original.role.replace('_', ' ')}</span>
    ),
  },
  {
    accessorKey: 'created_at',
    header: 'Joined',
    cell: ({ row }) => (
      <span className="text-sm text-slate-500">{formatDate(row.original.created_at)}</span>
    ),
  },
  {
    id: 'action',
    header: '',
    cell: ({ row }) => (
      <Link to={`/users/${row.original.id}`} className="text-xs font-medium text-indigo-600 hover:text-indigo-800">
        View →
      </Link>
    ),
  },
];