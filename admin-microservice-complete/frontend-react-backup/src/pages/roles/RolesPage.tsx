import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ShieldCheck, ShieldAlert, ShieldOff, Users } from 'lucide-react';
import {
  PageShell, PageHeader, Button, DataTable,
} from '@/components/ui';
import { cn } from '@/lib/utils';
import { adminApi } from '@/api/admin.api';
import { ROLES, ROLE_PERMISSIONS, ROLE_META, PERMISSION_GROUPS, type Role, type Permission } from '@/utils/permissions';
import { usePermissions } from '@/hooks/usePermissions';
import {
  getRoleUsersColumns, getPermissionCompareColumns, buildPermissionCompareRows,
} from '../_shared/listColumns';

const ROLE_ICONS: Record<Role, React.ReactNode> = {
  super_admin: <ShieldAlert size={18} className="text-red-500" />,
  admin: <ShieldCheck size={18} className="text-indigo-500" />,
  parlor_owner: <ShieldOff size={18} className="text-violet-500" />,
  user: <Users size={18} className="text-slate-400" />,
};

export default function RolesPage() {
  const [selectedRole, setSelectedRole] = useState<Role>('admin');
  const { isSuperAdmin } = usePermissions();
  const currentPerms = ROLE_PERMISSIONS[selectedRole];
  const meta = ROLE_META[selectedRole];

  const { data: roleUsers, isLoading: usersLoading } = useQuery({
    queryKey: ['role-users', selectedRole],
    queryFn: () => adminApi.getUsers({ role: selectedRole, limit: 10 }),
  });

  const roleUserColumns = useMemo(() => getRoleUsersColumns(), []);
  const compareColumns = useMemo(() => getPermissionCompareColumns(), []);
  const compareRows = useMemo(() => buildPermissionCompareRows(), []);

  return (
    <PageShell>
      <PageHeader title="Roles & Permissions" subtitle="RBAC configuration and role assignments" />

      {!isSuperAdmin && (
        <div className="gc-alert-info">View only. Only Super Admins can modify role permissions.</div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
        <div className="space-y-3">
          <h3 className="gc-section-title px-1">Select Role</h3>
          {(Object.values(ROLES) as Role[]).map(role => {
            const m = ROLE_META[role];
            const permCount = ROLE_PERMISSIONS[role].length;
            const isSelected = selectedRole === role;
            return (
              <button key={role} type="button" onClick={() => setSelectedRole(role)}
                className={cn('w-full flex items-start gap-3 p-4 rounded-2xl border text-left transition-all',
                  isSelected ? 'border-indigo-500 bg-indigo-50 shadow-sm' : 'border-slate-200 bg-white hover:border-slate-300 gc-card-flat')}>
                <div className="mt-0.5">{ROLE_ICONS[role]}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-semibold text-sm text-slate-800">{m.label}</span>
                    {role === 'super_admin' && <span className="gc-badge bg-red-100 text-red-600">Full Access</span>}
                  </div>
                  <p className="gc-section-subtitle">{m.desc}</p>
                  <div className="mt-2 flex items-center gap-1.5">
                    <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                      <div className={cn('h-full rounded-full', isSelected ? 'bg-indigo-500' : 'bg-slate-400')}
                        style={{ width: `${role === 'super_admin' ? 100 : role === 'admin' ? 85 : role === 'parlor_owner' ? 15 : 0}%` }} />
                    </div>
                    <span className="text-xs text-slate-400">{permCount} perms</span>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        <div className="lg:col-span-2 gc-card-flat overflow-hidden">
          <div className="gc-card-header flex items-center justify-between flex-wrap gap-3">
            <div className="flex items-center gap-2">
              {ROLE_ICONS[selectedRole]}
              <div>
                <h3 className="gc-section-title">{meta.label}</h3>
                <p className="gc-section-subtitle">{currentPerms.length} permissions active</p>
              </div>
            </div>
            {isSuperAdmin && selectedRole !== 'super_admin' && <Button size="sm">Save Changes</Button>}
          </div>
          <div className="divide-y divide-slate-50 max-h-[600px] overflow-y-auto">
            {PERMISSION_GROUPS.map(group => (
              <div key={group.label} className="px-4 sm:px-5 py-4">
                <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">{group.label}</h4>
                <div className="space-y-2">
                  {group.perms.map(perm => {
                    const active = currentPerms.includes(perm.key);
                    const locked = selectedRole === 'super_admin';
                    return (
                      <div key={perm.key}
                        className={cn('flex items-center gap-3 p-2.5 rounded-xl transition-colors', active ? 'bg-emerald-50' : 'hover:bg-slate-50')}>
                        <div className={cn('relative flex-shrink-0 w-10 h-5 rounded-full transition-colors', locked || active ? 'bg-emerald-500' : 'bg-slate-300')}>
                          <div className={cn('absolute top-0.5 w-4 h-4 bg-white rounded-full shadow-sm transition-transform', active ? 'left-5' : 'left-0.5')} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className={cn('text-sm font-medium', active ? 'text-slate-800' : 'text-slate-400')}>{perm.label}</div>
                          <div className="gc-section-subtitle">{perm.desc}</div>
                        </div>
                        {active && <span className="text-xs text-emerald-600 font-medium flex-shrink-0">✓ Active</span>}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <DataTable
        title={`${meta.label} Users`}
        subtitle={`${roleUsers?.items.length ?? 0} users with this role`}
        columns={roleUserColumns}
        data={roleUsers?.items ?? []}
        isLoading={usersLoading}
        emptyMessage="No users with this role"
      />

      <DataTable
        title="Permission Comparison"
        subtitle="Quick reference across all roles"
        columns={compareColumns}
        data={compareRows}
        emptyMessage="No permissions defined"
        compact
      />
    </PageShell>
  );
}