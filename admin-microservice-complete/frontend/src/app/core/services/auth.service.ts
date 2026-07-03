import { HttpClient } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';
import { canAccessAdmin } from '../constants/permissions';
import { AuthResponse, User } from '../models';

const TOKEN_KEY = 'gc_access_token';
const REFRESH_KEY = 'gc_refresh_token';
const USER_KEY = 'gc_user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly base = environment.apiUrl;

  readonly currentUser = signal<User | null>(this.readStoredUser());
  readonly isAuthenticated = computed(() => this.currentUser() !== null);

  constructor() {
    this.restoreSession();
  }

  loginWithPassword(username: string, password: string): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${this.base}/auth/login`, { username, password })
      .pipe(tap((res) => this.setSession(res)));
  }

  requestLoginOtp(phoneNumber: string): Observable<{ message: string; success: boolean }> {
    return this.http.post<{ message: string; success: boolean }>(
      `${this.base}/auth/login/request-otp`,
      { phone_number: phoneNumber },
    );
  }

  verifyLoginOtp(phoneNumber: string, otp: string): Observable<AuthResponse> {
    return this.http
      .post<AuthResponse>(`${this.base}/auth/login/verify-otp`, {
        phone_number: phoneNumber,
        otp,
      })
      .pipe(tap((res) => this.setSession(res)));
  }

  refreshToken(): Observable<AuthResponse> {
    const refreshToken = localStorage.getItem(REFRESH_KEY);
    return this.http
      .post<AuthResponse>(`${this.base}/auth/refresh-token`, { refresh_token: refreshToken })
      .pipe(tap((res) => this.setSession(res)));
  }

  logout(): void {
    const refreshToken = localStorage.getItem(REFRESH_KEY);
    if (refreshToken) {
      this.http.post(`${this.base}/auth/logout`, { refresh_token: refreshToken }).subscribe();
    }
    this.clearSession();
    this.router.navigate(['/login']);
  }

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  }

  isAdmin(): boolean {
    const role = this.currentUser()?.role;
    return role === 'admin' || role === 'super_admin';
  }

  isSuperAdmin(): boolean {
    return this.currentUser()?.role === 'super_admin';
  }

  canAccessAdminPanel(): boolean {
    const role = this.currentUser()?.role;
    return role ? canAccessAdmin(role) : false;
  }

  private setSession(res: AuthResponse): void {
    localStorage.setItem(TOKEN_KEY, res.access_token);
    localStorage.setItem(REFRESH_KEY, res.refresh_token);
    localStorage.setItem(USER_KEY, JSON.stringify(res.user));
    this.currentUser.set(res.user);
  }

  private clearSession(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    this.currentUser.set(null);
  }

  private readStoredUser(): User | null {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  }

  private restoreSession(): void {
    if (this.getToken() && !this.currentUser()) {
      this.http.get<User>(`${this.base}/auth/me`).subscribe({
        next: (user) => {
          localStorage.setItem(USER_KEY, JSON.stringify(user));
          this.currentUser.set(user);
        },
        error: () => this.clearSession(),
      });
    }
  }
}