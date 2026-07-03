import { Link } from 'react-router-dom';
import type { ColumnDef } from '@tanstack/react-table';
import { BadgeCheck, BadgeX, Trash2, Star, Store, Eye } from 'lucide-react';
import type { Parlor } from '@/types';
import { PERMISSIONS, type Permission } from '@/utils/permissions';
import TableCellUser from '@/components/ui/TableCellUser';
import TableCellActions from '@/components/ui/TableCellActions';
import StatusBadge from '@/components/ui/StatusBadge';

export interface ParlorsColumnOptions {
  can: (p: Permission) => boolean;
  onVerify: (id: string, verified: boolean) => void;
  onDelete: (parlor: Parlor) => void;
}

export function getParlorsColumns(opts: ParlorsColumnOptions): ColumnDef<Parlor>[] {
  const { can, onVerify, onDelete } = opts;

  return [
    {
      id: 'parlor',
      header: 'Parlor',
      cell: ({ row }) => (
        <TableCellUser
          name={row.original.name}
          subtitle={row.original.address}
          square
          imageUrl={row.original.logo_url}
          avatar={!row.original.logo_url ? (
            <div className="gc-table-avatar-square bg-violet-100">
              <Store size={14} className="text-violet-600" />
            </div>
          ) : undefined}
          avatarColor="bg-violet-100 text-violet-600"
        />
      ),
    },
    {
      id: 'owner',
      header: 'Owner',
      cell: ({ row }) => (
        <div>
          <div className="gc-table-cell-primary">{row.original.owner_name}</div>
          <div className="gc-table-cell-sub">{row.original.owner_phone}</div>
        </div>
      ),
    },
    {
      id: 'games',
      header: 'Games',
      cell: ({ row }) => (
        <div className="flex flex-wrap gap-1 max-w-48">
          {(row.original.game_types ?? []).slice(0, 3).map(g => (
            <span key={g} className="gc-badge bg-slate-100 text-slate-600">{g}</span>
          ))}
          {(row.original.game_types?.length ?? 0) > 3 && (
            <span className="gc-badge bg-slate-100 text-slate-400">
              +{row.original.game_types!.length - 3}
            </span>
          )}
        </div>
      ),
      enableSorting: false,
    },
    {
      id: 'rating',
      header: 'Rating',
      accessorFn: row => row.avg_rating,
      cell: ({ row }) => (
        <div className="flex items-center gap-1 text-amber-500">
          <Star size={12} fill="currentColor" />
          <span className="gc-table-cell-primary">{row.original.avg_rating.toFixed(1)}</span>
          <span className="gc-table-cell-sub">({row.original.rating_count})</span>
        </div>
      ),
    },
    {
      accessorKey: 'follower_count',
      header: 'Followers',
      cell: ({ row }) => (
        <span className="tabular-nums text-slate-600">{row.original.follower_count.toLocaleString()}</span>
      ),
    },
    {
      id: 'status',
      header: 'Status',
      cell: ({ row }) => (
        <StatusBadge status={row.original.is_verified ? 'verified' : 'unverified'} />
      ),
      enableSorting: false,
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => {
        const parlor = row.original;
        return (
          <TableCellActions>
            <Link to={`/parlors/${parlor.id}`} className="gc-table-action-btn" title="View detail">
              <Eye size={14} />
            </Link>
            {can(PERMISSIONS.VERIFY_PARLORS) && !parlor.is_verified && (
              <button
                onClick={() => onVerify(parlor.id, true)}
                className="gc-table-action-btn text-emerald-500 hover:bg-emerald-50"
                title="Verify"
              >
                <BadgeCheck size={14} />
              </button>
            )}
            {can(PERMISSIONS.VERIFY_PARLORS) && parlor.is_verified && (
              <button
                onClick={() => onVerify(parlor.id, false)}
                className="gc-table-action-btn text-amber-500 hover:bg-amber-50"
                title="Unverify"
              >
                <BadgeX size={14} />
              </button>
            )}
            {can(PERMISSIONS.DELETE_PARLORS) && (
              <button
                onClick={() => onDelete(parlor)}
                className="gc-table-action-btn text-red-500 hover:bg-red-50"
                title="Delete"
              >
                <Trash2 size={14} />
              </button>
            )}
          </TableCellActions>
        );
      },
      enableSorting: false,
    },
  ];
}