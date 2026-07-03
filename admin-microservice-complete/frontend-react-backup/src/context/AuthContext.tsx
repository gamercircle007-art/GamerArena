import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, AuthTokens } from '../types';

interface AuthStore {
  user: User | null; accessToken: string | null; refreshToken: string | null; isAuthenticated: boolean;
  login: (user: User, tokens: AuthTokens) => void;
  logout: () => void;
  updateTokens: (t: { access_token: string }) => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null, accessToken: null, refreshToken: null, isAuthenticated: false,
      login: (user, tokens) => {
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('refresh_token', tokens.refresh_token);
        set({ user, accessToken: tokens.access_token, refreshToken: tokens.refresh_token, isAuthenticated: true });
      },
      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({ user: null, accessToken: null, refreshToken: null, isAuthenticated: false });
      },
      updateTokens: (t) => {
        localStorage.setItem('access_token', t.access_token);
        set({ accessToken: t.access_token });
      },
    }),
    { name: 'gc-admin-auth', partialize: s => ({ user: s.user, accessToken: s.accessToken, refreshToken: s.refreshToken, isAuthenticated: s.isAuthenticated }) }
  )
);
