import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  input,
  output,
} from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { animate, state, style, transition, trigger } from '@angular/animations';
import { hasPermission } from '../../../core/constants/permissions';
import { UserRole } from '../../../core/models';
import { AuthService } from '../../../core/services/auth.service';

interface NavItem {
  label: string;
  icon: string;
  route: string;
  permission?: string;
  superAdminOnly?: boolean;
  badge?: number;
}

interface NavSection {
  section: string;
  items: NavItem[];
}

const NAV_CONFIG: NavSection[] = [
  {
    section: 'OVERVIEW',
    items: [
      { label: 'Dashboard', icon: 'bi-speedometer2', route: '/dashboard' },
      {
        label: 'Analytics',
        icon: 'bi-bar-chart-line',
        route: '/analytics',
        permission: 'view_platform_analytics',
      },
    ],
  },
  {
    section: 'MANAGEMENT',
    items: [
      { label: 'Users', icon: 'bi-people', route: '/users', permission: 'view_users' },
      { label: 'Parlors', icon: 'bi-shop', route: '/parlors', permission: 'view_parlors' },
      {
        label: 'Tournaments',
        icon: 'bi-trophy',
        route: '/tournaments',
        permission: 'view_tournaments',
      },
      {
        label: 'Bookings',
        icon: 'bi-ticket-perforated',
        route: '/bookings',
        permission: 'view_all_bookings',
      },
      {
        label: 'Slots',
        icon: 'bi-clock-history',
        route: '/slots',
        permission: 'view_all_bookings',
      },
      {
        label: 'Offers',
        icon: 'bi-tag',
        route: '/offers',
        permission: 'view_all_bookings',
      },
      { label: 'Events', icon: 'bi-calendar-event', route: '/events', permission: 'view_events' },
    ],
  },
  {
    section: 'CONTENT',
    items: [
      { label: 'Posts', icon: 'bi-file-text', route: '/posts', permission: 'view_posts' },
      {
        label: 'Reels & Videos',
        icon: 'bi-camera-video',
        route: '/posts/reels',
        permission: 'view_posts',
      },
      {
        label: 'Comments',
        icon: 'bi-chat-dots',
        route: '/social/comments',
        permission: 'view_comments',
      },
      { label: 'Likes', icon: 'bi-heart', route: '/social/likes', permission: 'view_likes' },
      {
        label: 'Community',
        icon: 'bi-globe2',
        route: '/community',
        permission: 'view_community',
      },
    ],
  },
  {
    section: 'SOCIAL',
    items: [
      { label: 'Geo Activity', icon: 'bi-geo-alt', route: '/geo', permission: 'view_geo' },
      { label: 'Ratings', icon: 'bi-star', route: '/ratings', permission: 'view_ratings' },
    ],
  },
  {
    section: 'SYSTEM',
    items: [
      {
        label: 'Broadcast',
        icon: 'bi-megaphone',
        route: '/notifications',
        permission: 'send_broadcast',
      },
      { label: 'Roles & Perms', icon: 'bi-shield-check', route: '/roles', superAdminOnly: true },
      { label: 'Settings', icon: 'bi-gear', route: '/settings', superAdminOnly: true },
    ],
  },
];

@Component({
  selector: 'app-sidebar',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, RouterLinkActive],
  animations: [
    trigger('sidebarState', [
      state('expanded', style({ width: '260px', minWidth: '260px' })),
      state('collapsed', style({ width: '70px', minWidth: '70px' })),
      transition('expanded <=> collapsed', animate('300ms cubic-bezier(0.4, 0, 0.2, 1)')),
    ]),
    trigger('textFade', [
      state('expanded', style({ opacity: 1, transform: 'translateX(0)' })),
      state('collapsed', style({ opacity: 0, transform: 'translateX(-10px)', display: 'none' })),
      transition('expanded <=> collapsed', animate('200ms ease')),
    ]),
  ],
  template: `
    <nav
      class="sidebar"
      [class.sidebar--mobile-open]="mobileOpen()"
      [@sidebarState]="collapsed() ? 'collapsed' : 'expanded'">
      <div class="sidebar-brand">
        <div class="brand-icon">
          <i class="bi bi-controller fs-5 text-white"></i>
        </div>
        @if (!collapsed()) {
          <div class="brand-text" [@textFade]="collapsed() ? 'collapsed' : 'expanded'">
            <span class="brand-name">GameConnect</span>
            <span class="brand-sub">Admin Panel <span class="version-tag">v1.0</span></span>
          </div>
        }
      </div>

      <div class="sidebar-nav">
        @for (section of visibleSections(); track section.section) {
          @if (!collapsed()) {
            <div class="nav-section-label">{{ section.section }}</div>
          }
          @for (item of section.items; track item.route) {
            <a
              class="nav-item"
              [routerLink]="item.route"
              routerLinkActive="active"
              [title]="collapsed() ? item.label : ''"
              (click)="navigate.emit()"
            >
              <i class="bi {{ item.icon }} nav-icon"></i>
              @if (!collapsed()) {
                <span class="nav-label" [@textFade]="collapsed() ? 'collapsed' : 'expanded'">
                  {{ item.label }}
                </span>
              }
              @if (item.badge && item.badge > 0 && !collapsed()) {
                <span class="badge bg-danger nav-badge">{{ item.badge }}</span>
              }
            </a>
          }
        }
      </div>

      @if (!collapsed()) {
        <div class="sidebar-footer">
          <div class="user-info">
            <div class="user-avatar">{{ userInitial() }}</div>
            <div class="user-details">
              <span class="user-name">{{ auth.currentUser()?.name ?? 'Admin' }}</span>
              <span class="user-role badge bg-primary">{{ auth.currentUser()?.role }}</span>
            </div>
          </div>
          <button type="button" class="btn-logout" (click)="logout()" title="Logout">
            <i class="bi bi-box-arrow-right"></i>
          </button>
        </div>
      }
    </nav>
  `,
  styles: `
    .sidebar {
      height: 100vh;
      background: #283046;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      position: sticky;
      top: 0;
      flex-shrink: 0;
      z-index: 200;
    }
    .sidebar-brand {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 20px 18px;
      border-bottom: 1px solid rgba(255,255,255,0.1);
      min-height: 72px;
    }
    .brand-icon {
      width: 36px;
      height: 36px;
      background: #7367f0;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .brand-name { color: #fff; font-size: 14px; font-weight: 700; display: block; }
    .brand-sub { color: rgba(255,255,255,0.5); font-size: 10px; }
    .version-tag {
      background: rgba(115,103,240,0.3);
      padding: 1px 5px;
      border-radius: 4px;
      margin-left: 4px;
    }
    .sidebar-nav { flex: 1; overflow-y: auto; padding: 12px 10px; }
    .sidebar-nav::-webkit-scrollbar { width: 4px; }
    .sidebar-nav::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
    .nav-section-label {
      color: rgba(255,255,255,0.35);
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      padding: 14px 10px 5px;
    }
    .nav-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 9px 12px;
      border-radius: 6px;
      color: rgba(255,255,255,0.65);
      text-decoration: none;
      margin-bottom: 2px;
      transition: all 0.15s;
      white-space: nowrap;
      overflow: hidden;
    }
    .nav-item:hover { background: rgba(255,255,255,0.05); color: #fff; }
    .nav-item.active {
      background: linear-gradient(118deg, #7367f0, rgba(115,103,240,0.7));
      box-shadow: 0 0 10px 1px rgba(115,103,240,0.5);
      color: #fff;
    }
    .nav-icon { font-size: 16px; flex-shrink: 0; width: 18px; text-align: center; }
    .nav-label { font-size: 13px; font-weight: 400; flex: 1; }
    .nav-badge { font-size: 10px; }
    .sidebar-footer {
      padding: 14px;
      border-top: 1px solid rgba(255,255,255,0.1);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .user-info { display: flex; align-items: center; gap: 10px; flex: 1; min-width: 0; }
    .user-avatar {
      width: 34px;
      height: 34px;
      background: #7367f0;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-weight: 700;
      font-size: 13px;
      flex-shrink: 0;
    }
    .user-details { min-width: 0; }
    .user-name {
      color: #fff;
      font-size: 12px;
      font-weight: 600;
      display: block;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .user-role { font-size: 9px; text-transform: uppercase; }
    .btn-logout {
      background: none;
      border: none;
      color: rgba(255,255,255,0.4);
      padding: 6px;
      border-radius: 6px;
      cursor: pointer;
      transition: color 0.15s;
      flex-shrink: 0;
    }
    .btn-logout:hover { color: #ea5455; }

    @media (max-width: 768px) {
      .sidebar {
        position: fixed;
        left: 0;
        top: 0;
        transform: translateX(-100%);
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: none;
      }

      .sidebar.sidebar--mobile-open {
        transform: translateX(0);
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.2);
      }
    }
  `,
})
export class SidebarComponent {
  protected readonly auth = inject(AuthService);
  readonly collapsed = input(false);
  readonly mobileOpen = input(false);
  readonly navigate = output<void>();

  readonly userInitial = computed(
    () => this.auth.currentUser()?.name?.[0]?.toUpperCase() ?? 'A',
  );

  readonly visibleSections = computed(() => {
    const user = this.auth.currentUser();
    const role = (user?.role ?? 'user') as UserRole;
    const isSuperAdmin = role === 'super_admin';

    return NAV_CONFIG.map((section) => ({
      ...section,
      items: section.items.filter((item) => {
        if (item.superAdminOnly && !isSuperAdmin) return false;
        if (item.permission && !hasPermission(role, item.permission)) return false;
        return true;
      }),
    })).filter((section) => section.items.length > 0);
  });

  logout(): void {
    this.auth.logout();
  }
}