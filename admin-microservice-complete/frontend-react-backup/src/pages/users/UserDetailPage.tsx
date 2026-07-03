import { useMemo, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Ban, CheckCircle, Trash2, UserCog,
  Ticket, Heart, Users, Mail, Phone, Calendar,
} from 'lucide-react';
import { toast } from 'sonner';
import {
  PageShell, DetailHeader, Card, Button, StatCard, DataTable,
  ConfirmModal, StatusBadge, CardSkeleton,
} from '../../components/ui';
import { getUserBookingsColumns } from '../_shared/listColumns';
import { cn } from '../../utils/cn';
import { adminApi } from '../../api/admin.api';
import { usePermissions } from '../../hooks/usePermissions';
import { PERMISSIONS, ROLE_META } from '../../utils/permissions';
import { formatDate, timeAgo } from '../../utils/formatters';
import type { User } from '../../types';

export default function UserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { can } = usePermissions();

  const [confirm, setConfirm] = useState<{ type: 'ban' | 'unban' | 'delete'; user: User } | null>(null);
  const [roleModal, setRoleModal] = useState(false);

  const { data: user, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-user', id],
    queryFn: () => adminApi.getUser(id!),
    enabled: !!id,
  });

  const { data: bookings, isLoading: bookingsLoading } = useQuery({
    queryKey: ['admin-user-bookings', id],
    queryFn: () => adminApi.getBookings({ user_id: id, limit: 5, page: 1 }),
    enabled: !!id,
  });

  const updateMutation = useMutation({
    mutationFn: (data: { is_active?: boolean; role?: string }) =>
      adminApi.updateUser(id!, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-user', id] });
      qc.invalidateQueries({ queryKey: ['admin-users'] });
      toast.success('User updated');
      setConfirm(null);
      setRoleModal(false);
    },
    onError: () => toast.error('Action failed'),
  });

  const deleteMutation = useMutation({
    mutationFn: () => adminApi.deleteUser(id!),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin-users'] });
      toast.success('User deleted');
      navigate('/users');
    },
    onError: () => toast.error('Delete failed'),
  });

  const execConfirm = () => {
    if (!confirm || !user) return;
    if (confirm.type === 'ban') updateMutation.mutate({ is_active: false });
    if (confirm.type === 'unban') updateMutation.mutate({ is_active: true });
    if (confirm.type === 'delete') deleteMutation.mutate();
  };

  const bookingColumns = useMemo(() => getUserBookingsColumns(), []);

  if (isLoading) {
    return (
      <PageShell>
        <CardSkeleton className="h-8 w-48" />
        <CardSkeleton className="h-40" />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {Array.from({ length: 3 }).map((_, i) => <CardSkeleton key={i} />)}
        </div>
      </PageShell>
    );
  }

  if (isError || !user) {
    return (
      <PageShell>
        <Card padding className="text-center py-12">
          <p className="text-slate-500 mb-4">User not found or failed to load.</p>
          <div className="flex items-center justify-center gap-4">
            <Button variant="ghost" onClick={() => refetch()}>Retry</Button>
            <Link to="/users" className="text-sm text-slate-500 hover:text-indigo-600">← Back to Users</Link>
          </div>
        </Card>
      </PageShell>
    );
  }

  const roleMeta = ROLE_META[user.role];

  return (
    <PageShell>
      <DetailHeader
        onBack={() => navigate('/users')}
        title={user.name}
        subtitle={`User ID: ${user.id}`}
        actions={
          <>
            {can(PERMISSIONS.CHANGE_ROLE) && (
              <Button variant="secondary" onClick={() => setRoleModal(true)}>
                <UserCog size={14} /> Edit Role
              </Button>
            )}
            {can(PERMISSIONS.BAN_USERS) && user.is_active && (
              <Button variant="secondary" onClick={() => setConfirm({ type: 'ban', user })} className="text-orange-600 border-orange-200 hover:bg-orange-50">
                <Ban size={14} /> Ban
              </Button>
            )}
            {can(PERMISSIONS.BAN_USERS) && !user.is_active && (
              <Button variant="secondary" onClick={() => setConfirm({ type: 'unban', user })} className="text-emerald-600 border-emerald-200 hover:bg-emerald-50">
                <CheckCircle size={14} /> Unban
              </Button>
            )}
            {can(PERMISSIONS.DELETE_USERS) && (
              <Button variant="danger" onClick={() => setConfirm({ type: 'delete', user })}>
                <Trash2 size={14} /> Delete
              </Button>
            )}
          </>
        }
      />

      <Card padding>
        <div className="flex flex-col sm:flex-row gap-6">
          {user.avatar_url ? (
            <img src={user.avatar_url} alt="" className="w-20 h-20 rounded-full object-cover flex-shrink-0" />
          ) : (
            <div className="w-20 h-20 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 text-2xl font-bold flex-shrink-0">
              {user.name?.[0]?.toUpperCase()}
            </div>
          )}
          <div className="flex-1 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <InfoRow icon={Phone} label="Phone" value={user.phone ?? '—'} />
            <InfoRow icon={Mail} label="Email" value={user.email ?? '—'} />
            <div>
              <div className="gc-label mb-1">Role</div>
              <span className={cn('gc-badge', roleMeta.bg, roleMeta.color)}>{roleMeta.label}</span>
              {user.parlor_name && <div className="gc-section-subtitle mt-1">{user.parlor_name}</div>}
            </div>
            <div>
              <div className="gc-label mb-1">Status</div>
              <StatusBadge status={user.is_active ? 'active' : 'banned'} />
            </div>
            <InfoRow icon={Calendar} label="Joined" value={`${formatDate(user.created_at)} (${timeAgo(user.created_at)})`} />
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
        <StatCard title="Bookings" value={user.bookings_count ?? 0} Icon={Ticket} color="green" />
        <StatCard title="Posts Liked" value={user.likes_count ?? 0} Icon={Heart} color="pink" />
        <StatCard title="Following" value={user.following_count ?? 0} Icon={Users} color="indigo" />
      </div>

      <DataTable
        title="Recent Bookings"
        subtitle="Last 5 bookings by this user"
        columns={bookingColumns}
        data={bookings?.items ?? []}
        isLoading={bookingsLoading}
        emptyMessage="No bookings yet"
      />
      {(bookings?.total ?? 0) > 5 && (
        <div className="text-center">
          <Link to={`/bookings?user=${user.id}`} className="text-xs text-indigo-600 hover:underline">
            View all {bookings?.total} bookings →
          </Link>
        </div>
      )}

      <ConfirmModal
        isOpen={!!confirm}
        danger={confirm?.type === 'delete'}
        title={confirm?.type === 'ban' ? 'Ban User' : confirm?.type === 'unban' ? 'Unban User' : 'Delete User'}
        message={
          confirm?.type === 'ban' ? `Ban "${user.name}"? They won't be able to login.` :
          confirm?.type === 'unban' ? `Unban "${user.name}"? They can login again.` :
          `Permanently delete "${user.name}"? This cannot be undone.`
        }
        confirmLabel={confirm?.type === 'ban' ? 'Ban' : confirm?.type === 'unban' ? 'Unban' : 'Delete'}
        onConfirm={execConfirm}
        onCancel={() => setConfirm(null)}
        loading={updateMutation.isPending || deleteMutation.isPending}
      />

      {roleModal && (
        <div className="gc-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="role-modal-title">
          <div className="gc-modal-backdrop" onClick={() => setRoleModal(false)} />
          <div className="gc-modal-panel">
            <h3 id="role-modal-title" className="text-lg font-semibold mb-1">Change Role</h3>
            <p className="text-sm text-slate-500 mb-4">Change role for <strong>{user.name}</strong></p>
            <div className="space-y-2">
              {(['user', 'parlor_owner', 'admin', 'super_admin'] as const).map(r => (
                <button
                  key={r}
                  onClick={() => updateMutation.mutate({ role: r })}
                  className={cn(
                    'w-full flex items-center justify-between px-4 py-3 border rounded-lg text-sm hover:border-indigo-400 transition-colors',
                    user.role === r && 'border-indigo-500 bg-indigo-50',
                  )}
                >
                  <span className="font-medium capitalize">{r.replace('_', ' ')}</span>
                  {user.role === r && <span className="text-xs text-indigo-600">Current</span>}
                </button>
              ))}
            </div>
            <Button variant="ghost" onClick={() => setRoleModal(false)} className="mt-4 w-full">Cancel</Button>
          </div>
        </div>
      )}
    </PageShell>
  );
}

function InfoRow({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2">
      <Icon size={14} className="text-slate-400 mt-0.5 flex-shrink-0" aria-hidden />
      <div>
        <div className="gc-label mb-0">{label}</div>
        <div className="text-sm text-slate-700">{value}</div>
      </div>
    </div>
  );
}