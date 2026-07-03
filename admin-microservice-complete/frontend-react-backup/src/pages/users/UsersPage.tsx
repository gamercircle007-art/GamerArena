import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Download } from 'lucide-react';
import { toast } from 'sonner';
import {
  PageShell, PageHeader, FilterBar, SearchInput, Select, Button, DataTable, ConfirmModal,
} from '@/components/ui';
import { adminApi } from '@/api/admin.api';
import { usePermissions } from '@/hooks/usePermissions';
import { useDebounce } from '@/hooks/useDebounce';
import { PERMISSIONS } from '@/utils/permissions';
import type { User } from '@/types';
import { getUsersColumns } from './usersColumns';

export default function UsersPage() {
  const qc = useQueryClient();
  const { can, isSuperAdmin } = usePermissions();
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 300);
  const [roleFilter, setRoleFilter] = useState('');
  const [activeFilter, setActiveFilter] = useState('');
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [confirm, setConfirm] = useState<{ type: 'ban' | 'unban' | 'delete' | 'bulk-ban' | 'bulk-delete'; user?: User } | null>(null);
  const [roleModal, setRoleModal] = useState<User | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-users', page, debouncedSearch, roleFilter, activeFilter],
    queryFn: () => adminApi.getUsers({
      page,
      search: debouncedSearch,
      ...(roleFilter ? { role: roleFilter } : {}),
      ...(activeFilter !== '' ? { is_active: activeFilter === 'true' } : {}),
    }),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data: d }: { id: string; data: { is_active?: boolean; role?: string } }) => adminApi.updateUser(id, d),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-users'] });
      toast.success('User updated');
      setConfirm(null);
      setRoleModal(null);
      setSelected(new Set());
    },
    onError: () => toast.error('Action failed'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => adminApi.deleteUser(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-users'] });
      toast.success('User deleted');
      setConfirm(null);
      setSelected(new Set());
    },
    onError: () => toast.error('Delete failed'),
  });

  const items = data?.items ?? [];
  const allSelected = items.length > 0 && items.every(u => selected.has(u.id));
  const total = data?.total ?? 0;
  const pages = data?.pages ?? 1;

  const toggleAll = () => setSelected(allSelected ? new Set() : new Set(items.map(u => u.id)));
  const toggleOne = (id: string) => {
    const n = new Set(selected);
    n.has(id) ? n.delete(id) : n.add(id);
    setSelected(n);
  };

  const exportCsv = () => {
    const rows = [['Name', 'Phone', 'Email', 'Role', 'Status', 'Joined'], ...items.map(u => [
      u.name, u.phone ?? '', u.email ?? '', u.role, u.is_active ? 'active' : 'banned', u.created_at,
    ])];
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([rows.map(r => r.join(',')).join('\n')], { type: 'text/csv' }));
    a.download = 'users-export.csv';
    a.click();
  };

  const execConfirm = async () => {
    if (!confirm) return;
    if (confirm.type === 'ban' && confirm.user) updateMutation.mutate({ id: confirm.user.id, data: { is_active: false } });
    if (confirm.type === 'unban' && confirm.user) updateMutation.mutate({ id: confirm.user.id, data: { is_active: true } });
    if (confirm.type === 'delete' && confirm.user) deleteMutation.mutate(confirm.user.id);
    if (confirm.type === 'bulk-ban') {
      for (const id of selected) await adminApi.updateUser(id, { is_active: false });
      qc.invalidateQueries({ queryKey: ['admin-users'] });
      toast.success(`Banned ${selected.size} users`);
      setConfirm(null);
      setSelected(new Set());
    }
    if (confirm.type === 'bulk-delete') {
      for (const id of selected) await adminApi.deleteUser(id);
      qc.invalidateQueries({ queryKey: ['admin-users'] });
      toast.success(`Deleted ${selected.size} users`);
      setConfirm(null);
      setSelected(new Set());
    }
  };

  const columns = useMemo(() => getUsersColumns({
    selected,
    allSelected,
    toggleAll,
    toggleOne,
    can,
    onBan: user => setConfirm({ type: 'ban', user }),
    onUnban: user => setConfirm({ type: 'unban', user }),
    onDelete: user => setConfirm({ type: 'delete', user }),
    onChangeRole: setRoleModal,
  }), [selected, allSelected, items, can]);

  return (
    <PageShell>
      <PageHeader
        title="Users"
        subtitle="Manage platform users, roles, and access"
        onExport={exportCsv}
      />

      <FilterBar footer={selected.size > 0 ? (
        <div className="flex flex-wrap items-center gap-2 pt-3">
          <span className="text-xs text-slate-500">{selected.size} selected</span>
          {can(PERMISSIONS.BAN_USERS) && (
            <Button variant="secondary" size="sm" onClick={() => setConfirm({ type: 'bulk-ban' })}>Bulk Ban</Button>
          )}
          {can(PERMISSIONS.DELETE_USERS) && (
            <Button variant="danger" size="sm" onClick={() => setConfirm({ type: 'bulk-delete' })}>Bulk Delete</Button>
          )}
        </div>
      ) : undefined}>
        <SearchInput
          placeholder="Search name, phone, email..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1); }}
        />
        <Select value={roleFilter} onChange={e => { setRoleFilter(e.target.value); setPage(1); }} className="w-auto min-w-[8rem]">
          <option value="">All Roles</option>
          <option value="user">User</option>
          <option value="parlor_owner">Parlor Owner</option>
          <option value="admin">Admin</option>
          {isSuperAdmin && <option value="super_admin">Super Admin</option>}
        </Select>
        <Select value={activeFilter} onChange={e => { setActiveFilter(e.target.value); setPage(1); }} className="w-auto min-w-[8rem]">
          <option value="">All Status</option>
          <option value="true">Active</option>
          <option value="false">Banned</option>
        </Select>
        <span className="text-sm text-slate-400 ml-auto">{total} users</span>
      </FilterBar>

      <DataTable
        columns={columns}
        data={items}
        isLoading={isLoading}
        isError={isError}
        onRetry={() => refetch()}
        emptyMessage="No users found"
        pagination={{ page, pages, total, onPageChange: setPage }}
      />

      <ConfirmModal
        isOpen={!!confirm}
        danger={confirm?.type?.includes('delete')}
        title={
          confirm?.type === 'ban' ? 'Ban User'
          : confirm?.type === 'unban' ? 'Unban User'
          : confirm?.type === 'bulk-ban' ? `Ban ${selected.size} Users`
          : confirm?.type === 'bulk-delete' ? `Delete ${selected.size} Users`
          : 'Delete User'
        }
        message={
          confirm?.type === 'ban' ? `Ban "${confirm.user?.name}"?`
          : confirm?.type === 'unban' ? `Unban "${confirm.user?.name}"?`
          : confirm?.type === 'bulk-ban' ? `Ban ${selected.size} selected users?`
          : confirm?.type === 'bulk-delete' ? `Permanently delete ${selected.size} users?`
          : `Delete "${confirm?.user?.name}"?`
        }
        confirmLabel={confirm?.type?.includes('delete') ? 'Delete' : 'Confirm'}
        onConfirm={execConfirm}
        onCancel={() => setConfirm(null)}
        loading={updateMutation.isPending || deleteMutation.isPending}
      />

      {roleModal && (
        <div className="gc-modal-overlay" role="dialog" aria-modal="true">
          <div className="gc-modal-backdrop" onClick={() => setRoleModal(null)} />
          <div className="gc-modal-panel">
            <h3 className="text-lg font-semibold mb-1">Change Role</h3>
            <p className="text-sm text-slate-500 mb-4">Change role for <strong>{roleModal.name}</strong></p>
            <div className="space-y-2">
              {(['user', 'parlor_owner', 'admin', 'super_admin'] as const).map(r => (
                <button
                  key={r}
                  type="button"
                  onClick={() => updateMutation.mutate({ id: roleModal.id, data: { role: r } })}
                  className={`w-full flex items-center justify-between px-4 py-3 border rounded-xl text-sm transition-colors ${
                    roleModal.role === r ? 'border-primary bg-indigo-50' : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <span className="font-medium capitalize">{r.replace('_', ' ')}</span>
                  {roleModal.role === r && <span className="text-xs text-primary">Current</span>}
                </button>
              ))}
            </div>
            <Button variant="ghost" className="w-full mt-4" onClick={() => setRoleModal(null)}>Cancel</Button>
          </div>
        </div>
      )}
    </PageShell>
  );
}