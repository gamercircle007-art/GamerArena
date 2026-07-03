import { Link } from 'react-router-dom';
import type { ColumnDef } from '@tanstack/react-table';
import { Ban, CheckCircle, Trash2, UserCog, Eye } from 'lucide-react';
import type { User } from '@/types';
import { PERMISSIONS, type Permission } from '@/utils/permissions';
import TableCheckbox from '@/components/ui/TableCheckbox';
import TableCellUser from '@/components/ui/TableCellUser';
import TableCellActions from '@/components/ui/TableCellActions';
import StatusBadge from '@/components/ui/StatusBadge';
import { formatDate, timeAgo } from '@/utils/formatters';

const ROLE_COLORS: Record<string, string> = {
  super_admin: 'bg-red-100 text-red-700',
  admin: 'bg-indigo-100 text-indigo-700',
  parlor_owner: 'bg-violet-100 text-violet-700',
  user: 'bg-slate-100 text-slate-600',
};

export interface UsersColumnOptions {
  selected: Set<string>;
  allSelected: boolean;
  toggleAll: () => void;
  toggleOne: (id: string) => void;
  can: (p: Permission) => boolean;
  onBan: (user: User) => void;
  onUnban: (user: User) => void;
  onDelete: (user: User) => void;
  onChangeRole: (user: User) => void;
}

export function getUsersColumns(opts: UsersColumnOptions): ColumnDef<User>[] {
  const { selected, allSelected, toggleAll, toggleOne, can, onBan, onUnban, onDelete, onChangeRole } = opts;

  return [
    {
      id: 'select',
      header: () => (
        <TableCheckbox checked={allSelected} onChange={toggleAll} label="Select all" />
      ),
      cell: ({ row }) => (
        <TableCheckbox
          checked={selected.has(row.original.id)}
          onChange={() => toggleOne(row.original.id)}
          label={`Select ${row.original.name}`}
        />
      ),
      size: 40,
      enableSorting: false,
    },
    {
      id: 'user',
      header: 'User',
      cell: ({ row }) => (
        <TableCellUser name={row.original.name} subtitle={row.original.parlor_name} />
      ),
    },
    {
      id: 'contact',
      header: 'Contact',
      cell: ({ row }) => (
        <div>
          <div className="gc-table-cell-primary">{row.original.phone}</div>
          <div className="gc-table-cell-sub">{row.original.email}</div>
        </div>
      ),
    },
    {
      accessorKey: 'role',
      header: 'Role',
      cell: ({ row }) => (
        <span className={`gc-badge ${ROLE_COLORS[row.original.role] ?? ROLE_COLORS.user}`}>
          {row.original.role.replace('_', ' ')}
        </span>
      ),
    },
    {
      id: 'status',
      header: 'Status',
      cell: ({ row }) => (
        <StatusBadge status={row.original.is_active ? 'active' : 'banned'} />
      ),
    },
    {
      accessorKey: 'created_at',
      header: 'Joined',
      cell: ({ row }) => (
        <div className="text-sm text-slate-500">
          <div>{formatDate(row.original.created_at)}</div>
          <div className="text-xs text-slate-400">{timeAgo(row.original.created_at)}</div>
        </div>
      ),
    },
    {
      id: 'actions',
      header: '',
      cell: ({ row }) => {
        const user = row.original;
        return (
          <TableCellActions>
            <Link to={`/users/${user.id}`} className="gc-table-action-btn" title="View">
              <Eye size={14} />
            </Link>
            {can(PERMISSIONS.BAN_USERS) && user.is_active && (
              <button onClick={() => onBan(user)} className="gc-table-action-btn text-orange-500 hover:bg-orange-50" title="Ban">
                <Ban size={14} />
              </button>
            )}
            {can(PERMISSIONS.BAN_USERS) && !user.is_active && (
              <button onClick={() => onUnban(user)} className="gc-table-action-btn text-emerald-500 hover:bg-emerald-50" title="Unban">
                <CheckCircle size={14} />
              </button>
            )}
            {can(PERMISSIONS.CHANGE_ROLE) && (
              <button onClick={() => onChangeRole(user)} className="gc-table-action-btn text-indigo-500 hover:bg-indigo-50" title="Role">
                <UserCog size={14} />
              </button>
            )}
            {can(PERMISSIONS.DELETE_USERS) && (
              <button onClick={() => onDelete(user)} className="gc-table-action-btn text-red-500 hover:bg-red-50" title="Delete">
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