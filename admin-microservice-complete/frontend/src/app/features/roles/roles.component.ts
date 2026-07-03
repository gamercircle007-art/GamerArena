import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal,
} from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  bootstrapCheckLg,
  bootstrapPeople,
  bootstrapShieldCheck,
  bootstrapShieldExclamation,
  bootstrapShieldX,
  bootstrapX,
} from '@ng-icons/bootstrap-icons';

import { PERMISSIONS, ROLE_PERMISSIONS } from '../../core/constants/permissions';
import { UserRole } from '../../core/models';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';

interface PermissionItem {
  key: string;
  label: string;
  description: string;
}

interface PermissionGroup {
  label: string;
  perms: PermissionItem[];
}

const ROLE_META: Record<UserRole, { label: string; description: string; coverage: number }> = {
  super_admin: {
    label: 'Super Admin',
    description: 'Full unrestricted access to all platform features',
    coverage: 100,
  },
  admin: {
    label: 'Admin',
    description: 'Manage users, content, tournaments, and analytics',
    coverage: 85,
  },
  parlor_owner: {
    label: 'Parlor Owner',
    description: 'Own parlor analytics, bookings, and events',
    coverage: 15,
  },
  user: {
    label: 'User',
    description: 'No admin panel access',
    coverage: 0,
  },
};

const PERMISSION_GROUPS: PermissionGroup[] = [
  {
    label: 'Users',
    perms: [
      { key: PERMISSIONS.VIEW_USERS, label: 'View Users', description: 'See all user accounts' },
      { key: PERMISSIONS.BAN_USERS, label: 'Ban/Unban Users', description: 'Restrict user login access' },
      { key: PERMISSIONS.DELETE_USERS, label: 'Delete Users', description: 'Remove accounts permanently' },
    ],
  },
  {
    label: 'Parlors',
    perms: [
      { key: PERMISSIONS.VIEW_PARLORS, label: 'View Parlors', description: 'Browse all gaming parlors' },
      { key: PERMISSIONS.VERIFY_PARLORS, label: 'Verify Parlors', description: 'Grant verification badge' },
      { key: PERMISSIONS.DELETE_PARLORS, label: 'Delete Parlors', description: 'Remove parlor and data' },
    ],
  },
  {
    label: 'Content',
    perms: [
      { key: PERMISSIONS.VIEW_POSTS, label: 'View Posts', description: 'See all social posts' },
      { key: PERMISSIONS.DELETE_POSTS, label: 'Delete Posts', description: 'Remove posts from feed' },
      { key: PERMISSIONS.MODERATE_COMMENTS, label: 'Moderate Comments', description: 'Remove or restore comments' },
      { key: PERMISSIONS.VIEW_COMMUNITY, label: 'View Community', description: 'Access forum discussions' },
    ],
  },
  {
    label: 'Tournaments',
    perms: [
      { key: PERMISSIONS.VIEW_TOURNAMENTS, label: 'View Tournaments', description: 'See all tournaments' },
      { key: PERMISSIONS.MANAGE_TOURNAMENTS, label: 'Manage Tournaments', description: 'Change status and delete' },
      { key: PERMISSIONS.VIEW_ALL_BOOKINGS, label: 'View All Bookings', description: 'See every booking' },
      { key: PERMISSIONS.VIEW_EVENTS, label: 'View Events', description: 'See parlor events' },
    ],
  },
  {
    label: 'Analytics',
    perms: [
      { key: PERMISSIONS.VIEW_PLATFORM_ANALYTICS, label: 'Platform Analytics', description: 'Charts and growth data' },
      { key: PERMISSIONS.VIEW_RATINGS, label: 'View Ratings', description: 'See parlor reviews' },
      { key: PERMISSIONS.VIEW_GEO, label: 'Geo Activity', description: 'Location-tagged posts map' },
    ],
  },
  {
    label: 'System',
    perms: [
      { key: PERMISSIONS.SEND_BROADCAST, label: 'Send Broadcast', description: 'Push notifications to users' },
      { key: PERMISSIONS.MANAGE_ROLES, label: 'Manage Roles', description: 'Edit role permissions' },
      { key: PERMISSIONS.MANAGE_SETTINGS, label: 'Manage Settings', description: 'Platform configuration' },
    ],
  },
];

const ALL_ROLES: UserRole[] = ['super_admin', 'admin', 'parlor_owner', 'user'];

@Component({
  selector: 'app-roles',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [NgIcon, PageHeaderComponent],
  providers: [
    provideIcons({
      bootstrapShieldExclamation,
      bootstrapShieldCheck,
      bootstrapShieldX,
      bootstrapPeople,
      bootstrapCheckLg,
      bootstrapX,
    }),
  ],
  template: `
    <div class="roles-page">
      <app-page-header
        title="Roles & Permissions"
        subtitle="RBAC configuration and permission matrix"
        [breadcrumbs]="[{ label: 'Home', route: '/dashboard' }, { label: 'Roles' }]" />

      @if (!isSuperAdmin()) {
        <div class="alert alert-info mb-4">
          View only. Only Super Admins can modify role permissions.
        </div>
      }

      <div class="row g-4 mb-4">
        <!-- Role Cards -->
        <div class="col-lg-4">
          <h6 class="section-label mb-3">Select Role</h6>
          <div class="d-flex flex-column gap-3">
            @for (role of allRoles; track role) {
              <button
                type="button"
                class="role-card"
                [class.role-card--active]="selectedRole() === role"
                (click)="selectedRole.set(role)">
                <div class="role-card__icon">
                  <ng-icon [name]="roleIcon(role)" size="18" />
                </div>
                <div class="flex-grow-1 min-w-0 text-start">
                  <div class="d-flex align-items-center gap-2 flex-wrap">
                    <span class="fw-semibold">{{ roleMeta(role).label }}</span>
                    @if (role === 'super_admin') {
                      <span class="badge bg-danger-subtle text-danger">Full Access</span>
                    }
                  </div>
                  <p class="role-card__desc mb-2">{{ roleMeta(role).description }}</p>
                  <div class="d-flex align-items-center gap-2">
                    <div class="progress flex-grow-1 role-progress">
                      <div
                        class="progress-bar"
                        [style.width.%]="roleMeta(role).coverage"
                        [class.bg-primary]="selectedRole() === role"
                        [class.bg-secondary]="selectedRole() !== role">
                      </div>
                    </div>
                    <small class="text-muted">{{ permissionCount(role) }} perms</small>
                  </div>
                </div>
              </button>
            }
          </div>
        </div>

        <!-- Permission Matrix -->
        <div class="col-lg-8">
          <div class="card matrix-card h-100">
            <div class="card-header border-0 bg-white d-flex justify-content-between align-items-start flex-wrap gap-2">
              <div class="d-flex align-items-center gap-2">
                <ng-icon [name]="roleIcon(selectedRole())" size="20" />
                <div>
                  <h6 class="mb-0 fw-bold">{{ roleMeta(selectedRole()).label }}</h6>
                  <small class="text-muted">{{ activePermissions().length }} permissions active</small>
                </div>
              </div>
              @if (isSuperAdmin() && selectedRole() !== 'super_admin') {
                <button type="button" class="btn btn-sm btn-primary" (click)="saveChanges()">
                  Save Changes
                </button>
              }
            </div>
            <div class="card-body matrix-body">
              @for (group of permissionGroups; track group.label) {
                <div class="permission-group">
                  <h6 class="group-label">{{ group.label }}</h6>
                  @for (perm of group.perms; track perm.key) {
                    <div
                      class="permission-row"
                      [class.permission-row--active]="hasRolePermission(selectedRole(), perm.key)">
                      <div class="form-check form-switch permission-switch">
                        <input
                          class="form-check-input"
                          type="checkbox"
                          role="switch"
                          [id]="'perm-' + selectedRole() + '-' + perm.key"
                          [checked]="hasRolePermission(selectedRole(), perm.key)"
                          [disabled]="isPermissionLocked(selectedRole())"
                          (change)="togglePermission(perm.key, $any($event.target).checked)" />
                      </div>
                      <div class="flex-grow-1">
                        <div class="fw-medium permission-name">{{ perm.label }}</div>
                        <small class="text-muted">{{ perm.description }}</small>
                      </div>
                      @if (hasRolePermission(selectedRole(), perm.key)) {
                        <span class="badge bg-success-subtle text-success">Active</span>
                      }
                    </div>
                  }
                </div>
              }
            </div>
          </div>
        </div>
      </div>

      <!-- Comparison Table -->
      <div class="card comparison-card">
        <div class="card-header border-0 bg-white">
          <h6 class="mb-0 fw-bold">Permission Comparison</h6>
          <small class="text-muted">Quick reference across all roles</small>
        </div>
        <div class="card-body p-0 table-responsive">
          <table class="table comparison-table mb-0">
            <thead>
              <tr>
                <th>Permission</th>
                @for (role of allRoles; track role) {
                  <th class="text-center">{{ roleMeta(role).label }}</th>
                }
              </tr>
            </thead>
            <tbody>
              @for (row of comparisonRows(); track row.key) {
                <tr>
                  <td>
                    <span class="fw-medium">{{ row.label }}</span>
                    <small class="d-block text-muted">{{ row.description }}</small>
                  </td>
                  @for (role of allRoles; track role) {
                    <td class="text-center">
                      @if (hasRolePermission(role, row.key)) {
                        <ng-icon name="bootstrapCheckLg" size="18" class="text-success" />
                      } @else {
                        <ng-icon name="bootstrapX" size="18" class="text-muted opacity-50" />
                      }
                    </td>
                  }
                </tr>
              }
            </tbody>
          </table>
        </div>
      </div>
    </div>
  `,
  styles: `
    .section-label {
      font-weight: 700;
      font-size: 0.875rem;
      color: #5e5873;
      padding-left: 0.25rem;
    }

    .role-card {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
      width: 100%;
      padding: 1rem 1.25rem;
      border: 2px solid #ebe9f1;
      border-radius: 1rem;
      background: #fff;
      transition: border-color 0.2s, box-shadow 0.2s;
    }

    .role-card:hover { border-color: #d8d6de; }

    .role-card--active {
      border-color: #7367f0;
      background: rgba(115, 103, 240, 0.04);
      box-shadow: 0 4px 12px rgba(115, 103, 240, 0.12);
    }

    .role-card__icon {
      margin-top: 0.125rem;
      color: #7367f0;
      flex-shrink: 0;
    }

    .role-card__desc {
      font-size: 0.8125rem;
      color: #b9b9c3;
      margin: 0;
      line-height: 1.4;
    }

    .role-progress { height: 6px; background: #f3f2f7; }

    .matrix-card .card-header { padding: 1.25rem 1.5rem 0.75rem; }

    .matrix-body {
      max-height: 600px;
      overflow-y: auto;
      padding: 0 1.5rem 1.5rem;
    }

    .permission-group { padding-top: 1rem; }

    .group-label {
      font-size: 0.6875rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #b9b9c3;
      margin-bottom: 0.75rem;
    }

    .permission-row {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.625rem 0.75rem;
      border-radius: 0.75rem;
      margin-bottom: 0.375rem;
      transition: background 0.15s;
    }

    .permission-row:hover { background: #f8f8f8; }
    .permission-row--active { background: rgba(40, 199, 111, 0.06); }

    .permission-switch { margin: 0; padding-left: 2.5rem; flex-shrink: 0; }
    .permission-switch .form-check-input:disabled { opacity: 1; cursor: not-allowed; }

    .permission-name { font-size: 0.875rem; color: #5e5873; }

    .comparison-card .card-header { padding: 1.25rem 1.5rem 0.5rem; }

    .comparison-table th {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      color: #b9b9c3;
      border-bottom-width: 1px;
      white-space: nowrap;
    }

    .comparison-table td {
      vertical-align: middle;
      font-size: 0.875rem;
      padding: 0.875rem 1rem;
    }

    .comparison-table tbody tr:hover { background: #fafafa; }
  `,
})
export class RolesComponent {
  private readonly auth = inject(AuthService);
  private readonly toast = inject(ToastService);

  readonly selectedRole = signal<UserRole>('admin');
  readonly permissionOverrides = signal<Partial<Record<UserRole, Set<string>>>>({});

  readonly allRoles = ALL_ROLES;
  readonly permissionGroups = PERMISSION_GROUPS;

  readonly isSuperAdmin = computed(() => this.auth.isSuperAdmin());

  readonly activePermissions = computed(() => {
    const role = this.selectedRole();
    return this.getEffectivePermissions(role);
  });

  readonly comparisonRows = computed(() =>
    PERMISSION_GROUPS.flatMap(g => g.perms),
  );

  roleMeta(role: UserRole) {
    return ROLE_META[role];
  }

  roleIcon(role: UserRole): string {
    const icons: Record<UserRole, string> = {
      super_admin: 'bootstrapShieldExclamation',
      admin: 'bootstrapShieldCheck',
      parlor_owner: 'bootstrapShieldX',
      user: 'bootstrapPeople',
    };
    return icons[role];
  }

  permissionCount(role: UserRole): number {
    const perms = ROLE_PERMISSIONS[role] ?? [];
    return perms.includes('*') ? PERMISSION_GROUPS.flatMap(g => g.perms).length : perms.length;
  }

  hasRolePermission(role: UserRole, permission: string): boolean {
    const base = ROLE_PERMISSIONS[role] ?? [];
    if (base.includes('*')) return true;

    const overrides = this.permissionOverrides()[role];
    if (overrides !== undefined) {
      return overrides.has(permission);
    }

    return base.includes(permission);
  }

  isPermissionLocked(role: UserRole): boolean {
    return role === 'super_admin' || !this.isSuperAdmin();
  }

  togglePermission(permission: string, enabled: boolean): void {
    const role = this.selectedRole();
    if (this.isPermissionLocked(role)) return;

    const overrides = { ...this.permissionOverrides() };
    const base = new Set<string>(ROLE_PERMISSIONS[role] ?? []);
    const current = overrides[role] ?? base;
    const next = new Set(current);

    if (enabled) {
      next.add(permission);
    } else {
      next.delete(permission);
    }

    overrides[role] = next;
    this.permissionOverrides.set(overrides);
  }

  saveChanges(): void {
    this.toast.success('Role permissions saved');
  }

  private getEffectivePermissions(role: UserRole): string[] {
    const base = ROLE_PERMISSIONS[role] ?? [];
    if (base.includes('*')) {
      return PERMISSION_GROUPS.flatMap(g => g.perms.map(p => p.key));
    }
    const override = this.permissionOverrides()[role];
    return override ? [...override] : [...base];
  }
}