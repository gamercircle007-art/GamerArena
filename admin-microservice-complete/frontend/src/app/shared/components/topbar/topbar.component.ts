import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  input,
  output,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NavigationEnd, Router } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { filter } from 'rxjs';
import { BsDropdownModule } from 'ngx-bootstrap/dropdown';
import { AuthService } from '../../../core/services/auth.service';
import { ThemeService } from '../../../core/services/theme.service';

const PAGE_TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/analytics': 'Analytics',
  '/users': 'Users',
  '/parlors': 'Parlors',
  '/tournaments': 'Tournaments',
  '/bookings': 'Bookings',
  '/events': 'Events',
  '/posts': 'Posts',
  '/posts/reels': 'Reels & Videos',
  '/social/comments': 'Comments',
  '/social/likes': 'Likes',
  '/community': 'Community',
  '/geo': 'Geo Activity',
  '/ratings': 'Ratings',
  '/notifications': 'Broadcast',
  '/roles': 'Roles & Permissions',
  '/settings': 'Settings',
};

@Component({
  selector: 'app-topbar',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, BsDropdownModule],
  template: `
    <header class="admin-topbar">
      <div class="topbar-left">
        <button
          type="button"
          class="btn btn-icon"
          (click)="toggleSidebar.emit()"
          aria-label="Toggle sidebar"
        >
          <i class="bi bi-list fs-5"></i>
        </button>
        <h1 class="page-title d-none d-sm-block">{{ pageTitle() }}</h1>
      </div>

      <div class="topbar-center d-none d-md-flex">
        <div class="search-box">
          <i class="bi bi-search search-icon"></i>
          <input
            type="search"
            class="form-control"
            placeholder="Search users, parlors, posts..."
            [(ngModel)]="searchQuery"
          />
        </div>
      </div>

      <div class="topbar-right">
        <button
          type="button"
          class="btn btn-icon"
          (click)="theme.toggle()"
          [attr.aria-label]="theme.isDark() ? 'Switch to light mode' : 'Switch to dark mode'">
          <i class="bi" [class.bi-moon]="!theme.isDark()" [class.bi-sun]="theme.isDark()"></i>
        </button>
        <button type="button" class="btn btn-icon position-relative d-none d-sm-inline-flex">
          <i class="bi bi-bell fs-5"></i>
          @if (notificationCount() > 0) {
            <span class="notif-badge">{{ notificationCount() }}</span>
          }
        </button>

        <div class="dropdown" dropdown>
          <button
            type="button"
            class="btn user-dropdown"
            dropdownToggle
            aria-label="User menu"
          >
            <div class="user-avatar-sm">{{ userInitial() }}</div>
            <span class="user-name-sm d-none d-lg-inline">{{ auth.currentUser()?.name }}</span>
            <i class="bi bi-chevron-down d-none d-lg-inline"></i>
          </button>
          <ul class="dropdown-menu dropdown-menu-end shadow" *dropdownMenu>
            <li class="dropdown-header">
              <strong>{{ auth.currentUser()?.name ?? 'Admin' }}</strong>
              <small class="d-block text-muted text-capitalize">{{ auth.currentUser()?.role }}</small>
            </li>
            <li><hr class="dropdown-divider" /></li>
            <li>
              <button type="button" class="dropdown-item">
                <i class="bi bi-person me-2"></i>Profile
              </button>
            </li>
            <li>
              <button type="button" class="dropdown-item">
                <i class="bi bi-key me-2"></i>Change Password
              </button>
            </li>
            <li><hr class="dropdown-divider" /></li>
            <li>
              <button type="button" class="dropdown-item text-danger" (click)="logout()">
                <i class="bi bi-box-arrow-right me-2"></i>Logout
              </button>
            </li>
          </ul>
        </div>
      </div>
    </header>
  `,
  styles: `
    .admin-topbar {
      height: var(--topbar-height);
      background: #fff;
      border-bottom: 1px solid #ebe9f1;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 1.25rem;
      box-shadow: 0 1px 4px rgba(0,0,0,0.06);
      position: sticky;
      top: 0;
      z-index: 100;
      gap: 1rem;
    }
    .topbar-left, .topbar-right {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-shrink: 0;
    }
    .topbar-center { flex: 1; max-width: 420px; }
    .page-title {
      font-size: 1.1rem;
      font-weight: 600;
      color: #5e5873;
      margin: 0;
    }
    .btn-icon {
      background: none;
      border: none;
      color: #6e6b7b;
      padding: 0.4rem 0.5rem;
      border-radius: 6px;
      line-height: 1;
    }
    .btn-icon:hover { background: #f8f8f8; color: #7367f0; }
    .search-box { position: relative; width: 100%; }
    .search-icon {
      position: absolute;
      left: 12px;
      top: 50%;
      transform: translateY(-50%);
      color: #b9b9c3;
      font-size: 14px;
      z-index: 1;
    }
    .search-box .form-control {
      padding-left: 2.25rem;
      border-radius: 20px;
      background: #f8f8f8;
      border-color: transparent;
    }
    .search-box .form-control:focus {
      background: #fff;
      border-color: #7367f0;
    }
    .notif-badge {
      position: absolute;
      top: 2px;
      right: 2px;
      background: #ea5455;
      color: #fff;
      font-size: 9px;
      font-weight: 700;
      min-width: 16px;
      height: 16px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0 4px;
    }
    .user-dropdown {
      display: flex;
      align-items: center;
      gap: 8px;
      background: none;
      border: none;
      padding: 4px 8px;
      border-radius: 8px;
      color: #5e5873;
    }
    .user-dropdown:hover { background: #f8f8f8; }
    .user-avatar-sm {
      width: 32px;
      height: 32px;
      background: #7367f0;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-weight: 700;
      font-size: 12px;
    }
    .user-name-sm { font-size: 13px; font-weight: 600; }
  `,
})
export class TopbarComponent {
  protected readonly auth = inject(AuthService);
  protected readonly theme = inject(ThemeService);
  private readonly router = inject(Router);

  readonly collapsed = input(false);
  readonly toggleSidebar = output<void>();

  searchQuery = '';
  readonly notificationCount = signal(3);
  private readonly currentPath = signal(this.router.url);

  readonly pageTitle = computed(() => {
    const path = this.currentPath().split('?')[0];
    if (PAGE_TITLES[path]) return PAGE_TITLES[path];
    if (path.startsWith('/users/')) return 'User Detail';
    const match = Object.keys(PAGE_TITLES)
      .sort((a, b) => b.length - a.length)
      .find((key) => path.startsWith(key));
    return match ? PAGE_TITLES[match] : 'Admin Panel';
  });

  readonly userInitial = computed(
    () => this.auth.currentUser()?.name?.[0]?.toUpperCase() ?? 'A',
  );

  constructor() {
    this.router.events
      .pipe(
        filter((e) => e instanceof NavigationEnd),
        takeUntilDestroyed(),
      )
      .subscribe((e) => this.currentPath.set((e as NavigationEnd).urlAfterRedirects));
  }

  logout(): void {
    this.auth.logout();
  }
}