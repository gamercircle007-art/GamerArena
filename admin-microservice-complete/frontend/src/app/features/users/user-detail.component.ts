import {
  ChangeDetectionStrategy,
  Component,
  computed,
  DestroyRef,
  inject,
  input,
  OnInit,
  signal,
  TemplateRef,
  ViewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  bootstrapArrowLeft,
  bootstrapCalendarCheck,
  bootstrapEnvelope,
  bootstrapHeart,
  bootstrapPerson,
  bootstrapPhone,
  bootstrapStar,
  bootstrapTrash,
  bootstrapPeople,
} from '@ng-icons/bootstrap-icons';
import { BsModalRef, BsModalService, ModalModule } from 'ngx-bootstrap/modal';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';

import { hasPermission, PERMISSIONS } from '../../core/constants/permissions';
import { Booking, Like, User, UserRole } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { StatsCardComponent } from '../../shared/components/stats-card/stats-card.component';
import { StatusBadgeComponent } from '../../shared/components/status-badge/status-badge.component';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';
import { TruncatePipe } from '../../shared/pipes/truncate.pipe';
import { ConfirmService } from '../../shared/services/confirm.service';

const CHANGEABLE_ROLES: UserRole[] = ['user', 'parlor_owner', 'admin', 'super_admin'];

@Component({
  selector: 'app-user-detail',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterLink,
    NgxDatatableModule,
    ModalModule,
    NgIcon,
    PageHeaderComponent,
    StatsCardComponent,
    StatusBadgeComponent,
    DateFormatPipe,
    TruncatePipe,
  ],
  providers: [
    provideIcons({
      bootstrapArrowLeft,
      bootstrapPerson,
      bootstrapPhone,
      bootstrapEnvelope,
      bootstrapCalendarCheck,
      bootstrapHeart,
      bootstrapPeople,
      bootstrapStar,
      bootstrapTrash,
    }),
  ],
  template: `
    <div class="user-detail-page">
      @if (loading()) {
        <div class="loading-state">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
        </div>
      } @else if (loadError() || !user()) {
        <div class="card error-card">
          <div class="card-body text-center py-5">
            <p class="text-muted mb-3">User not found or failed to load.</p>
            <div class="d-flex justify-content-center gap-2">
              <button type="button" class="btn btn-sm btn-primary" (click)="loadUser()">
                Retry
              </button>
              <a routerLink="/users" class="btn btn-sm btn-light">← Back to Users</a>
            </div>
          </div>
        </div>
      } @else {
        @if (user(); as u) {
          <app-page-header
            [title]="u.name || u.username || 'User'"
            [subtitle]="'User ID: ' + u.id"
            [breadcrumbs]="[
              { label: 'Home', route: '/dashboard' },
              { label: 'Users', route: '/users' },
              { label: u.name || u.username || 'Detail' },
            ]">
            <a routerLink="/users" class="btn btn-sm btn-light">
              <ng-icon name="bootstrapArrowLeft" size="14" class="me-1" />
              Back
            </a>
            @if (canChangeRole()) {
              <button type="button" class="btn btn-sm btn-outline-primary" (click)="openRoleModal()">
                Edit Role
              </button>
            }
            @if (canBan() && u.is_active) {
              <button
                type="button"
                class="btn btn-sm btn-outline-warning"
                [disabled]="actionLoading()"
                (click)="banUser()">
                Ban
              </button>
            }
            @if (canBan() && !u.is_active) {
              <button
                type="button"
                class="btn btn-sm btn-outline-success"
                [disabled]="actionLoading()"
                (click)="unbanUser()">
                Unban
              </button>
            }
            @if (canDelete()) {
              <button
                type="button"
                class="btn btn-sm btn-outline-danger"
                [disabled]="actionLoading()"
                (click)="deleteUser()">
                <ng-icon name="bootstrapTrash" size="14" class="me-1" />
                Delete
              </button>
            }
          </app-page-header>

          <!-- User Info Card -->
          <div class="card user-info-card mb-4">
            <div class="card-body">
              <div class="row g-4 align-items-start">
                <div class="col-auto">
                  <div class="profile-avatar">
                    @if (u.avatar_url) {
                      <img [src]="u.avatar_url" [alt]="u.name ?? 'User'" />
                    } @else {
                      <span class="avatar-letter">{{ avatarLetter(u) }}</span>
                    }
                  </div>
                </div>
                <div class="col">
                  <div class="row g-3 g-md-4">
                    <div class="col-sm-6 col-lg-3">
                      <div class="info-label">Phone</div>
                      <div class="info-value d-flex align-items-center gap-2">
                        <ng-icon name="bootstrapPhone" size="14" class="text-muted" />
                        {{ u.phone_number || '—' }}
                      </div>
                    </div>
                    <div class="col-sm-6 col-lg-3">
                      <div class="info-label">Email</div>
                      <div class="info-value d-flex align-items-center gap-2">
                        <ng-icon name="bootstrapEnvelope" size="14" class="text-muted" />
                        {{ u.email || '—' }}
                      </div>
                    </div>
                    <div class="col-sm-6 col-lg-3">
                      <div class="info-label">Role</div>
                      <span class="role-badge" [class]="'role-' + u.role">{{ formatRole(u.role) }}</span>
                      @if (u.parlor_name) {
                        <small class="text-muted d-block mt-1">{{ u.parlor_name }}</small>
                      }
                    </div>
                    <div class="col-sm-6 col-lg-3">
                      <div class="info-label">Status</div>
                      <app-status-badge [status]="u.is_active ? 'active' : 'banned'" />
                    </div>
                    <div class="col-sm-6 col-lg-3">
                      <div class="info-label">Joined</div>
                      <div class="info-value">{{ u.created_at | dateFormat }}</div>
                    </div>
                    @if (u.city) {
                      <div class="col-sm-6 col-lg-3">
                        <div class="info-label">Location</div>
                        <div class="info-value">{{ u.city }}{{ u.country ? ', ' + u.country : '' }}</div>
                      </div>
                    }
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Stats Row -->
          <div class="row g-3 g-xl-4 mb-4">
            <div class="col-6 col-xl-3">
              <app-stats-card
                title="Bookings"
                [value]="formatNumber(u.bookings_count)"
                icon="bootstrapCalendarCheck"
                color="success" />
            </div>
            <div class="col-6 col-xl-3">
              <app-stats-card
                title="Posts Liked"
                [value]="formatNumber(u.likes_count)"
                icon="bootstrapHeart"
                color="danger" />
            </div>
            <div class="col-6 col-xl-3">
              <app-stats-card
                title="Following"
                [value]="formatNumber(u.following_count)"
                icon="bootstrapPeople"
                color="primary" />
            </div>
            <div class="col-6 col-xl-3">
              <app-stats-card
                title="Reviews Written"
                [value]="formatNumber(u.reviews_count)"
                icon="bootstrapStar"
                color="warning" />
            </div>
          </div>

          <!-- Recent Bookings -->
          <div class="card table-card mb-4">
            <div class="card-header border-0 bg-white">
              <h6 class="mb-0 fw-bold">Recent Bookings</h6>
              <small class="text-muted">Last 5 bookings by this user</small>
            </div>
            <div class="card-body p-0">
              <ngx-datatable
                class="bootstrap detail-table"
                [rows]="bookings()"
                [columnMode]="ColumnMode.force"
                [headerHeight]="48"
                [rowHeight]="52"
                [footerHeight]="0"
                [scrollbarH]="true"
                [limit]="5">
                <ngx-datatable-column name="Event" [flexGrow]="2.5">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    <div class="fw-medium text-dark">
                      {{ row.tournament?.title || '—' }}
                    </div>
                    <small class="text-muted">{{ row.booking_type || 'tournament' }}</small>
                  </ng-template>
                </ngx-datatable-column>
                <ngx-datatable-column name="Parlor" [flexGrow]="2">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    {{ row.tournament?.parlor?.name || '—' }}
                  </ng-template>
                </ngx-datatable-column>
                <ngx-datatable-column name="Slot" [flexGrow]="1">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    #{{ row.slot_number }}
                  </ng-template>
                </ngx-datatable-column>
                <ngx-datatable-column name="Status" [flexGrow]="1.2">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    <app-status-badge [status]="row.status" />
                  </ng-template>
                </ngx-datatable-column>
                <ngx-datatable-column name="Date" [flexGrow]="1.5">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    {{ row.created_at | dateFormat }}
                  </ng-template>
                </ngx-datatable-column>
              </ngx-datatable>
              @if (!bookingsLoading() && !bookings().length) {
                <div class="empty-state">No bookings yet</div>
              }
            </div>
            @if (bookingsTotal() > 5) {
              <div class="card-footer bg-white border-0 text-center py-2">
                <a [routerLink]="['/bookings']" [queryParams]="{ user: u.id }" class="small text-primary">
                  View all {{ bookingsTotal() }} bookings →
                </a>
              </div>
            }
          </div>

          <!-- Recent Liked Posts -->
          <div class="card table-card">
            <div class="card-header border-0 bg-white">
              <h6 class="mb-0 fw-bold">Recent Liked Posts</h6>
              <small class="text-muted">Last 5 posts liked by this user</small>
            </div>
            <div class="card-body p-0">
              <ngx-datatable
                class="bootstrap detail-table"
                [rows]="likedPosts()"
                [columnMode]="ColumnMode.force"
                [headerHeight]="48"
                [rowHeight]="52"
                [footerHeight]="0"
                [scrollbarH]="true"
                [limit]="5">
                <ngx-datatable-column name="Post" [flexGrow]="3">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    <div class="text-dark">{{ row.target_preview | truncate: 80 }}</div>
                  </ng-template>
                </ngx-datatable-column>
                <ngx-datatable-column name="Parlor" [flexGrow]="2">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    {{ row.parlor_name || '—' }}
                  </ng-template>
                </ngx-datatable-column>
                <ngx-datatable-column name="Date" [flexGrow]="1.5">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    {{ row.created_at | dateFormat }}
                  </ng-template>
                </ngx-datatable-column>
              </ngx-datatable>
              @if (!likesLoading() && !likedPosts().length) {
                <div class="empty-state">No liked posts yet</div>
              }
            </div>
          </div>
        }
      }
    </div>

    <!-- Change Role Modal -->
    <ng-template #roleModalTpl>
      @if (user(); as u) {
        <div class="modal-header border-0 pb-0">
          <h5 class="modal-title fw-bold">Change Role</h5>
          <button type="button" class="btn-close" aria-label="Close" (click)="closeRoleModal()"></button>
        </div>
        <div class="modal-body pt-2">
          <p class="text-muted small mb-3">
            Select a new role for <strong>{{ u.name || u.username }}</strong>
          </p>
          <div class="role-options">
            @for (role of changeableRoles(); track role) {
              <button
                type="button"
                class="role-option"
                [class.role-option--active]="u.role === role"
                [disabled]="actionLoading()"
                (click)="changeRole(role)">
                <span class="fw-medium">{{ formatRole(role) }}</span>
                @if (u.role === role) {
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
    .loading-state {
      display: flex;
      justify-content: center;
      padding: 4rem 1rem;
    }

    .profile-avatar {
      width: 80px;
      height: 80px;
      border-radius: 50%;
      background: linear-gradient(118deg, #7367f0, rgba(115, 103, 240, 0.7));
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      font-size: 1.75rem;
      font-weight: 700;
    }

    .profile-avatar img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .info-label {
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #b9b9c3;
      margin-bottom: 0.25rem;
    }

    .info-value {
      font-size: 0.9375rem;
      color: #5e5873;
      font-weight: 500;
    }

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

    .detail-table { box-shadow: none; }

    .empty-state {
      padding: 2rem 1rem;
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
export class UserDetailComponent implements OnInit {
  @ViewChild('roleModalTpl') roleModalTpl!: TemplateRef<void>;

  readonly id = input.required<string>();

  private readonly api = inject(AdminApiService);
  private readonly auth = inject(AuthService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly modalService = inject(BsModalService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  private roleModalRef?: BsModalRef;

  readonly user = signal<User | null>(null);
  readonly bookings = signal<Booking[]>([]);
  readonly bookingsTotal = signal(0);
  readonly likedPosts = signal<Like[]>([]);
  readonly loading = signal(true);
  readonly loadError = signal(false);
  readonly bookingsLoading = signal(true);
  readonly likesLoading = signal(true);
  readonly actionLoading = signal(false);

  protected readonly ColumnMode = ColumnMode;

  readonly changeableRoles = computed(() => {
    if (this.auth.isSuperAdmin()) return CHANGEABLE_ROLES;
    return CHANGEABLE_ROLES.filter(r => r !== 'super_admin');
  });

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
    this.loadUser();
  }

  formatRole(role: UserRole): string {
    return role.replace(/_/g, ' ');
  }

  formatNumber(value: number | null | undefined): string {
    if (value === null || value === undefined) return '0';
    return value.toLocaleString('en-IN');
  }

  avatarLetter(user: User): string {
    return (user.name?.[0] || user.username?.[0] || '?').toUpperCase();
  }

  loadUser(): void {
    this.loading.set(true);
    this.loadError.set(false);

    this.api
      .getUser(this.id())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: user => {
          this.user.set(user);
          this.loading.set(false);
          this.loadBookings();
          this.loadLikedPosts();
        },
        error: () => {
          this.loading.set(false);
          this.loadError.set(true);
          this.toast.error('Failed to load user');
        },
      });
  }

  openRoleModal(): void {
    this.roleModalRef = this.modalService.show(this.roleModalTpl, {
      class: 'modal-dialog-centered',
    });
  }

  closeRoleModal(): void {
    this.roleModalRef?.hide();
  }

  changeRole(role: UserRole): void {
    const current = this.user();
    if (!current || current.role === role) return;
    this.patchUser({ role }, `Role changed to ${this.formatRole(role)}`, () => this.closeRoleModal());
  }

  async banUser(): Promise<void> {
    const current = this.user();
    if (!current) return;

    const confirmed = await this.confirm.confirm(
      'Ban User',
      `Ban "${current.name || current.username}"? They will lose access to the platform.`,
      'Ban',
      'warning',
    );
    if (!confirmed) return;
    this.patchUser({ is_active: false }, 'User banned');
  }

  unbanUser(): void {
    this.patchUser({ is_active: true }, 'User unbanned');
  }

  async deleteUser(): Promise<void> {
    const current = this.user();
    if (!current) return;

    const confirmed = await this.confirm.confirmDanger(
      'Delete User',
      `Permanently delete "${current.name || current.username}"? This cannot be undone.`,
    );
    if (!confirmed) return;

    this.actionLoading.set(true);
    this.api
      .deleteUser(current.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionLoading.set(false);
          this.toast.success('User deleted');
          this.router.navigate(['/users']);
        },
        error: () => {
          this.actionLoading.set(false);
          this.toast.error('Failed to delete user');
        },
      });
  }

  private loadBookings(): void {
    this.bookingsLoading.set(true);
    this.api
      .getBookings({ user_id: this.id(), page: 1, limit: 5 })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.bookings.set(res.items);
          this.bookingsTotal.set(res.total);
          this.bookingsLoading.set(false);
        },
        error: () => this.bookingsLoading.set(false),
      });
  }

  private loadLikedPosts(): void {
    this.likesLoading.set(true);
    this.api
      .getLikes({ user_id: this.id(), page: 1, limit: 5 })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.likedPosts.set(res.items);
          this.likesLoading.set(false);
        },
        error: () => this.likesLoading.set(false),
      });
  }

  private patchUser(
    data: Partial<Pick<User, 'is_active' | 'role'>>,
    successMessage: string,
    onSuccess?: () => void,
  ): void {
    const current = this.user();
    if (!current) return;

    this.actionLoading.set(true);
    this.api
      .updateUser(current.id, data)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: updated => {
          this.actionLoading.set(false);
          this.user.set({ ...current, ...updated, ...data });
          this.toast.success(successMessage);
          onSuccess?.();
        },
        error: () => {
          this.actionLoading.set(false);
          this.toast.error('Action failed');
        },
      });
  }
}