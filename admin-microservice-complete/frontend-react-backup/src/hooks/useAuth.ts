import { useAuthStore } from '../context/AuthContext';

export function useAuth() {
  const user = useAuthStore(s => s.user);
  const isAuthenticated = useAuthStore(s => s.isAuthenticated);
  const login = useAuthStore(s => s.login);
  const logout = useAuthStore(s => s.logout);
  return { user, isAuthenticated, login, logout, role: user?.role };
}