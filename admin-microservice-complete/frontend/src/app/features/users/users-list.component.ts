import {
  ChangeDetectionStrategy,
  Component,
  computed,
  DestroyRef,
  inject,
  OnInit,
  signal,
  TemplateRef,
  ViewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  bootstrapChevronDown,
  bootstrapPerson,
  bootstrapSearch,
  bootstrapThreeDotsVertical,
} from '@ng-icons/bootstrap-icons';
import { BsDropdownModule } from 'ngx-bootstrap/dropdown';
import { BsModalRef, BsModalService, ModalModule } from 'ngx-bootstrap/modal';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

import { hasPermission, PERMISSIONS } from '../../core/constants/permissions';
import { User, UserRole } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { AuthService } from '../../core/services/auth.service';
import { MockDataService } from '../../core/services/mock-data.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { StatusBadgeComponent } from '../../shared/components/status-badge/status-badge.component';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';
import { ConfirmService } from '../../shared/services/confirm.service';

type StatusFilter = '' | 'active' | 'banned';

const ROLE_OPTIONS: { value: UserRole | ''; label: string }[] = [
  { value: '', label: 'All Roles' },
  { value: 'user', label: 'User' },
  { value: 'parlor_owner', label: 'Parlor Owner' },
  { value: 'admin', label: 'Admin' },
  { value: 'super_admin', label: 'Super Admin' },
];

const CHANGEABLE_ROLES: UserRole[] = ['user', 'parlor_owner', 'admin', 'super_admin'];

@Component({
  selector: 'app-users-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    RouterLink,
    NgxDatatableModule,
    BsDropdownModule,
    ModalModule,
    NgIcon,
    PageHeaderComponent,
    StatusBadgeComponent,
    DateFormatPipe,
  ],
  providers: [
    provideIcons({
      bootstrapSearch,
      bootstrapPerson,
      bootstrapThreeDotsVertical,
      bootstrapChevronDown,
    }),
  ],
  template: `
    <div class="users-page">
      <app-page-header
        title="Users"
        subtitle="Manage platform users, roles, and access"
        [breadcrumbs]="[{ label: 'Home', route: '/dashboard' }, { label: 'Users' }]" />

      <!-- Filters -->
      <div class="card filters-card mb-4">
        <div class="card-body">
          <div class="row g-3 align-items-end">
            <div class="col-md-4">
              <label class="form-label small text-muted mb-1">Search</label>
              <div class="input-group">
                <span class="input-group-text bg-white border-end-0">
                  <ng-icon name="bootstrapSearch" size="16" class="text-muted" />
                </span>
                <input
                  type="search"
                  class="form-control border-start-0 ps-0"
                  placeholder="Search name, phone, email..."
                  [ngModel]="searchInput()"
                  (ngModelChange)="onSearchChange($event)" />
              </div>
            </div>
            <div class="col-md-3">
              <label class="form-label small text-muted mb-1">Role</label>
              <select
                class="form-select"
                [ngModel]="roleFilter()"
                (ngModelChange)="onRoleChange($event)">
                @for (opt of visibleRoleOptions(); track opt.value) {
                  <option [value]="opt.value">{{ opt.label }}</option>
                }
              </select>
            </div>
            <div class="col-md-3">
              <label class="form-label small text-muted mb-1">Status</label>
              <select
                class="form-select"
                [ngModel]="statusFilter()"
                (ngModelChange)="onStatusChange($event)">
                <option value="">All Status</option>
                <option value="active">Active</option>
                <option value="banned">Banned</option>
              </select>
            </div>
            <div class="col-md-2 text-md-end">
              <span class="badge bg-light text-dark results-badge">
                {{ total() }} user{{ total() === 1 ? '' : 's' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Table -->
      <div class="card table-card">
        <div class="card-body p-0">
          @if (loadError()) {
            <div class="error-state">
              <p class="mb-2">Failed to load users.</p>
              <button type="button" class="btn btn-sm btn-primary" (click)="loadUsers()">
                Retry
              </button>
            </div>
          } @else {
            <ngx-datatable
              class="bootstrap users-table"
              [rows]="rows()"
              [columnMode]="ColumnMode.force"
              [headerHeight]="48"
              [rowHeight]="56"
              [footerHeight]="56"
              [externalPaging]="true"
              [count]="total()"
              [offset]="page() - 1"
              [limit]="pageSize()"
              [scrollbarH]="true"
              [loadingIndicator]="loading()"
              (page)="onPage($event)"
              (sort)="onSort($event)">
              <ngx-datatable-column name="User" prop="name" [flexGrow]="2.5" [sortable]="true">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="d-flex align-items-center gap-2">
                    <div class="user-avatar">
                      @if (row.avatar_url) {
                        <img [src]="row.avatar_url" [alt]="row.name ?? 'User'" />
                      } @else {
                        <ng-icon name="bootstrapPerson" size="18" />
                      }
                    </div>
                    <div class="min-w-0">
                      <a
                        [routerLink]="['/users', row.id]"
                        class="fw-medium text-dark text-decoration-none user-name">
                        {{ row.name || row.username || '—' }}
                      </a>
                      @if (parlorName(row)) {
                        <small class="text-muted d-block text-truncate">{{ parlorName(row) }}</small>
                      }
                    </div>
                  </div>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Contact" [flexGrow]="2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="contact-cell">
                    <span>{{ row.phone_number || '—' }}</span>
                    <small class="text-muted d-block text-truncate">{{ row.email || '—' }}</small>
                  </div>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Role" prop="role" [flexGrow]="1.2" [sortable]="true">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="role-badge" [class]="'role-' + row.role">
                    {{ formatRole(row.role) }}
                  </span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Status" prop="is_active" [flexGrow]="1" [sortable]="true">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <app-status-badge [status]="row.is_active ? 'active' : 'banned'" />
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Joined" prop="created_at" [flexGrow]="1.2" [sortable]="true">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.created_at | dateFormat }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Actions" [flexGrow]="1" [sortable]="false" [resizeable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="dropdown" dropdown container="body" [dropup]="true">
                    <button
                      type="button"
                      class="btn btn-sm btn-light actions-btn"
                      dropdownToggle
                      aria-label="User actions">
                      <ng-icon name="bootstrapThreeDotsVertical" size="16" />
                    </button>
                    <ul *dropdownMenu class="dropdown-menu dropdown-menu-end shadow-sm">
                      <li>
                        <a class="dropdown-item" [routerLink]="['/users', row.id]">View</a>
                      </li>
                      @if (canBan() && row.is_active) {
                        <li>
                          <button
                            type="button"
                            class="dropdown-item text-warning"
                            [disabled]="actionUserId() === row.id"
                            (click)="banUser(row)">
                            Ban
                          </button>
                        </li>
                      }
                      @if (canBan() && !row.is_active) {
                        <li>
                          <button
                            type="button"
                            class="dropdown-item text-success"
                            [disabled]="actionUserId() === row.id"
                            (click)="unbanUser(row)">
                            Unban
                          </button>
                        </li>
                      }
                      @if (canChangeRole()) {
                        <li>
                          <button
                            type="button"
                            class="dropdown-item"
                            (click)="openRoleModal(row)">
                            Change Role
                          </button>
                        </li>
                      }
                      @if (canDelete()) {
                        <li><hr class="dropdown-divider" /></li>
                        <li>
                          <button
                            type="button"
                            class="dropdown-item text-danger"
                            [disabled]="actionUserId() === row.id"
                            (click)="deleteUser(row)">
                            Delete
                          </button>
                        </li>
                      }
                    </ul>
                  </div>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-footer>
                <ng-template
                  ngx-datatable-footer-template
                  let-rowCount="rowCount"
                  let-pageSize="pageSize"
                  let-curPage="curPage"
                  let-offset="offset">
                  <div class="datatable-footer-inner">
                    <div class="page-size-select">
                      <label class="small text-muted me-2">Rows</label>
                      <select
                        class="form-select form-select-sm"
                        [ngModel]="pageSize()"
                        (ngModelChange)="onPageSizeChange($event)">
                        @for (size of pageSizes; track size) {
                          <option [value]="size">{{ size }}</option>
                        }
                      </select>
                    </div>
                    <div class="pagination-info small text-muted">
                      {{ offset * pageSize + 1 }}–{{ endRow(offset, pageSize, rowCount) }}
                      of {{ total() }}
                    </div>
                    <div class="btn-group btn-group-sm">
                      <button
                        type="button"
                        class="btn btn-outline-secondary"
                        [disabled]="curPage <= 1"
                        (click)="setPage(curPage - 1)">
                        Prev
                      </button>
                      <button
                        type="button"
                        class="btn btn-outline-secondary"
                        [disabled]="curPage >= totalPages()"
                        (click)="setPage(curPage + 1)">
                        Next
                      </button>
                    </div>
                  </div>
                </ng-template>
              </ngx-datatable-footer>
            </ngx-datatable>

            @if (!loading() && !rows().length) {
              <div class="empty-state">No users found</div>
            }
          }
        </div>
      </div>
    </div>

    <!-- Change Role Modal -->
    <ng-template #roleModalTpl>
      @if (roleModalUser(); as user) {
        <div class="modal-header border-0 pb-0">
          <h5 class="modal-title fw-bold">Change Role</h5>
          <button type="button" class="btn-close" aria-label="Close" (click)="closeRoleModal()"></button>
        </div>
        <div class="modal-body pt-2">
          <p class="text-muted small mb-3">
            Select a new role for <strong>{{ user.name || user.username }}</strong>
          </p>
          <div class="role-options">
            @for (role of changeableRoles(); track role) {
              <button
                type="button"
                class="role-option"
                [class.role-option--active]="user.role === role"
                [disabled]="actionUserId() === user.id"
                (click)="changeRole(user, role)">
                <span class="fw-medium">{{ formatRole(role) }}</span>
                @if (user.role === role) {
                  <span class="badge bg-primary-subtle text-primary">Current</span>
                }
              </button>
            }
          </div>
        </div>
        <div class="modal-footer border-0 pt-0">
          <button type="button" class="btn btn-light" (click)="closeRoleModal()">Cancel</button>
        </div>
      }
    </ng-template>
  `,
  styles: `
    .filters-card .card-body { padding: 1.25rem 1.5rem; }

    .results-badge {
      font-size: 0.8125rem;
      font-weight: 600;
      padding: 0.5rem 0.75rem;
      border: 1px solid #ebe9f1;
    }

    .users-table { box-shadow: none; }

    .user-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: #f3f2f7;
      color: #7367f0;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      overflow: hidden;
    }

    .user-avatar img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .user-name:hover { color: #7367f0 !important; }

    .contact-cell { font-size: 0.875rem; line-height: 1.35; }

    .role-badge {
      display: inline-block;
      padding: 0.25rem 0.625rem;
      border-radius: 0.375rem;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: capitalize;
    }

    .role-user { background: #f3f2f7; color: #6e6b7b; }
    .role-parlor_owner { background: rgba(115, 103, 240, 0.12); color: #7367f0; }
    .role-admin { background: rgba(99, 102, 241, 0.12); color: #6366f1; }
    .role-super_admin { background: rgba(234, 84, 85, 0.12); color: #ea5455; }

    .actions-btn {
      border: 1px solid #ebe9f1;
      padding: 0.25rem 0.5rem;
    }

    .datatable-footer-inner {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 1rem;
      width: 100%;
      padding: 0.5rem 1rem;
    }

    .page-size-select {
      display: flex;
      align-items: center;
    }

    .page-size-select .form-select { width: auto; min-width: 4.5rem; }

    .empty-state,
    .error-state {
      padding: 2.5rem 1rem;
      text-align: center;
      color: #b9b9c3;
      font-size: 0.875rem;
    }

    .role-options { display: flex; flex-direction: column; gap: 0.5rem; }

    .role-option {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      padding: 0.75rem 1rem;
      border: 1px solid #ebe9f1;
      border-radius: 0.5rem;
      background: #fff;
      text-align: left;
      transition: border-color 0.2s, background 0.2s;
    }

    .role-option:hover:not(:disabled) {
      border-color: #7367f0;
      background: rgba(115, 103, 240, 0.04);
    }

    .role-option--active {
      border-color: #7367f0;
      background: rgba(115, 103, 240, 0.08);
    }

    .role-option:disabled { opacity: 0.6; cursor: not-allowed; }
  `,
})
export class UsersListComponent implements OnInit {
  @ViewChild('roleModalTpl') roleModalTpl!: TemplateRef<void>;

  private readonly api = inject(AdminApiService);
  private readonly auth = inject(AuthService);
  private readonly mock = inject(MockDataService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly modalService = inject(BsModalService);
  private readonly destroyRef = inject(DestroyRef);

  private readonly searchSubject = new Subject<string>();
  private roleModalRef?: BsModalRef;

  readonly rows = signal<User[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly pageSize = signal(20);
  readonly loading = signal(false);
  readonly loadError = signal(false);
  readonly searchInput = signal('');
  readonly roleFilter = signal<UserRole | ''>('');
  readonly statusFilter = signal<StatusFilter>('');
  readonly actionUserId = signal<string | null>(null);
  readonly roleModalUser = signal<User | null>(null);
  readonly sortProp = signal('created_at');
  readonly sortDir = signal<'asc' | 'desc'>('desc');

  readonly pageSizes = [10, 20, 50];

  protected readonly ColumnMode = ColumnMode;

  readonly visibleRoleOptions = computed(() => {
    if (this.auth.isSuperAdmin()) return ROLE_OPTIONS;
    return ROLE_OPTIONS.filter(o => o.value !== 'super_admin');
  });

  readonly changeableRoles = computed(() => {
    if (this.auth.isSuperAdmin()) return CHANGEABLE_ROLES;
    return CHANGEABLE_ROLES.filter(r => r !== 'super_admin');
  });

  readonly totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize())));

  readonly canBan = computed(() => {
    const role = this.auth.currentUser()?.role;
    return role ? hasPermission(role, PERMISSIONS.BAN_USERS) : false;
  });

  readonly canDelete = computed(() => {
    const role = this.auth.currentUser()?.role;
    return role ? hasPermission(role, PERMISSIONS.DELETE_USERS) : false;
  });

  readonly canChangeRole = computed(() => this.auth.isSuperAdmin());

  ngOnInit(): void {
    this.searchSubject
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe(term => {
        this.searchInput.set(term);
        this.page.set(1);
        this.loadUsers();
      });

    this.loadUsers();
  }

  onSearchChange(value: string): void {
    this.searchSubject.next(value);
  }

  onRoleChange(value: UserRole | ''): void {
    this.roleFilter.set(value);
    this.page.set(1);
    this.loadUsers();
  }

  onStatusChange(value: StatusFilter): void {
    this.statusFilter.set(value);
    this.page.set(1);
    this.loadUsers();
  }

  onPageSizeChange(size: number | string): void {
    this.pageSize.set(Number(size));
    this.page.set(1);
    this.loadUsers();
  }

  onPage(event: { offset: number }): void {
    this.page.set(event.offset + 1);
    this.loadUsers();
  }

  onSort(event: { sorts: { prop: string; dir: 'asc' | 'desc' }[] }): void {
    const sort = event.sorts[0];
    if (!sort) return;
    this.sortProp.set(String(sort.prop));
    this.sortDir.set(sort.dir);
    this.sortRows();
  }

  setPage(nextPage: number): void {
    if (nextPage < 1 || nextPage > this.totalPages()) return;
    this.page.set(nextPage);
    this.loadUsers();
  }

  endRow(offset: number, pageSize: number, rowCount: number): number {
    return Math.min(offset * pageSize + rowCount, this.total());
  }

  parlorName(user: User): string | null {
    if (user.role !== 'parlor_owner') return null;
    return this.mock.getParlorNameForOwner(user.id);
  }

  formatRole(role: UserRole): string {
    return role.replace(/_/g, ' ');
  }

  loadUsers(): void {
    this.loading.set(true);
    this.loadError.set(false);

    const params: Record<string, string | number | boolean> = {
      page: this.page(),
      limit: this.pageSize(),
    };

    const search = this.searchInput().trim();
    if (search) params['search'] = search;

    const role = this.roleFilter();
    if (role) params['role'] = role;

    const status = this.statusFilter();
    if (status === 'active') params['is_active'] = true;
    if (status === 'banned') params['is_active'] = false;

    this.api
      .getUsers(params)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.rows.set(res.items);
          this.total.set(res.total);
          this.sortRows();
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.loadError.set(true);
          this.toast.error('Failed to load users');
        },
      });
  }

  async banUser(user: User): Promise<void> {
    const confirmed = await this.confirm.confirm(
      'Ban User',
      `Ban "${user.name || user.username}"? They will lose access to the platform.`,
      'Ban',
      'warning',
    );
    if (!confirmed) return;
    this.patchUser(user.id, { is_active: false }, 'User banned');
  }

  unbanUser(user: User): void {
    this.patchUser(user.id, { is_active: true }, 'User unbanned');
  }

  openRoleModal(user: User): void {
    this.roleModalUser.set(user);
    this.roleModalRef = this.modalService.show(this.roleModalTpl, {
      class: 'modal-dialog-centered',
    });
  }

  closeRoleModal(): void {
    this.roleModalRef?.hide();
    this.roleModalUser.set(null);
  }

  changeRole(user: User, role: UserRole): void {
    if (user.role === role) return;
    this.patchUser(user.id, { role }, `Role changed to ${this.formatRole(role)}`, () => {
      this.closeRoleModal();
    });
  }

  async deleteUser(user: User): Promise<void> {
    const confirmed = await this.confirm.confirmDanger(
      'Delete User',
      `Permanently delete "${user.name || user.username}"? This cannot be undone.`,
    );
    if (!confirmed) return;

    this.actionUserId.set(user.id);
    this.api
      .deleteUser(user.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionUserId.set(null);
          this.toast.success('User deleted');
          this.loadUsers();
        },
        error: () => {
          this.actionUserId.set(null);
          this.toast.error('Failed to delete user');
        },
      });
  }

  private patchUser(
    id: string,
    data: Partial<Pick<User, 'is_active' | 'role'>>,
    successMessage: string,
    onSuccess?: () => void,
  ): void {
    this.actionUserId.set(id);
    this.api
      .updateUser(id, data)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionUserId.set(null);
          this.toast.success(successMessage);
          onSuccess?.();
          this.loadUsers();
        },
        error: () => {
          this.actionUserId.set(null);
          this.toast.error('Action failed');
        },
      });
  }

  private sortRows(): void {
    const prop = this.sortProp();
    const dir = this.sortDir();
    const multiplier = dir === 'asc' ? 1 : -1;

    const sorted = [...this.rows()].sort((a, b) => {
      const aVal = this.sortValue(a, prop);
      const bVal = this.sortValue(b, prop);
      if (aVal < bVal) return -1 * multiplier;
      if (aVal > bVal) return 1 * multiplier;
      return 0;
    });

    this.rows.set(sorted);
  }

  private sortValue(user: User, prop: string): string | number | boolean {
    if (prop === 'is_active') return user.is_active ? 1 : 0;
    const value = user[prop as keyof User];
    if (typeof value === 'boolean') return value ? 1 : 0;
    if (typeof value === 'number') return value;
    return String(value ?? '').toLowerCase();
  }
}