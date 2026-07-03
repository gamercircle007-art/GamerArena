import { useAuthStore } from '../context/AuthContext';
import { hasPermission, hasAnyPermission, canAccessAdmin, type Permission } from '../utils/permissions';

export function usePermissions() {
  const user = useAuthStore(s => s.user);
  const role = user?.role;
  return {
    role,
    can: (p: Permission) => hasPermission(role, p),
    canAny: (ps: Permission[]) => hasAnyPermission(role, ps),
    canAll: (ps: Permission[]) => ps.every(p => hasPermission(role, p)),
    canAccessAdmin: () => canAccessAdmin(role),
    isSuperAdmin: role === 'super_admin',
    isAdmin: role === 'admin' || role === 'super_admin',
    isOwner: role === 'parlor_owner',
  };
}
