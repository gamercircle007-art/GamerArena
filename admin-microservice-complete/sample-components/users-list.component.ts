// sample-components/users-list.component.ts
// COMPLETE EXAMPLE — shows ngx-datatable, signals, SweetAlert2, toastr, Bootstrap 5
// Use this as the pattern for ALL list pages.

import {
  Component, signal, computed, inject, OnInit, ChangeDetectionStrategy,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { NgxDatatableModule, ColumnMode, SelectionType } from '@swimlane/ngx-datatable';
import { ToastrService } from 'ngx-toastr';
import { NgIconsModule } from '@ng-icons/core';
import Swal from 'sweetalert2';
import { debounceTime, distinctUntilChanged, Subject, takeUntilDestroyed } from 'rxjs';
import { AdminApiService } from '../../core/services/admin-api.service';
import { AuthService } from '../../core/services/auth.service';
import { StatusBadgeComponent } from '../../shared/components/status-badge/status-badge.component';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';
import { User, PaginatedResponse } from '../../core/models';

@Component({
  selector: 'app-users-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule, RouterLink, NgxDatatableModule, NgIconsModule, StatusBadgeComponent, DateFormatPipe],
  template: `
    <div class="page-wrapper">

      <!-- Page header -->
      <div class="page-header d-flex align-items-center justify-content-between mb-4">
        <div>
          <h2 class="page-title">Users</h2>
          <nav aria-label="breadcrumb">
            <ol class="breadcrumb mb-0">
              <li class="breadcrumb-item"><a routerLink="/dashboard">Dashboard</a></li>
              <li class="breadcrumb-item active">Users</li>
            </ol>
          </nav>
        </div>
        <span class="badge bg-primary fs-6">{{ total() | number }} total</span>
      </div>

      <!-- Filter bar -->
      <div class="card shadow-sm mb-4">
        <div class="card-body py-3">
          <div class="row g-2 align-items-center">

            <div class="col-md-4">
              <div class="input-group">
                <span class="input-group-text bg-transparent border-end-0">
                  <ng-icon name="bootstrapSearch" size="14" />
                </span>
                <input type="text" class="form-control border-start-0 ps-0"
                  placeholder="Search name, phone, email..."
                  [(ngModel)]="searchTerm"
                  (ngModelChange)="onSearchChange($event)" />
              </div>
            </div>

            <div class="col-md-2">
              <select class="form-select form-select-sm" [(ngModel)]="roleFilter" (ngModelChange)="loadUsers()">
                <option value="">All Roles</option>
                <option value="user">User</option>
                <option value="parlor_owner">Parlor Owner</option>
                <option value="admin">Admin</option>
                @if (authService.isSuperAdmin()) {
                  <option value="super_admin">Super Admin</option>
                }
              </select>
            </div>

            <div class="col-md-2">
              <select class="form-select form-select-sm" [(ngModel)]="statusFilter" (ngModelChange)="loadUsers()">
                <option value="">All Status</option>
                <option value="true">Active</option>
                <option value="false">Banned</option>
              </select>
            </div>

            <div class="col-md-2">
              <button class="btn btn-outline-secondary btn-sm" (click)="resetFilters()">
                <ng-icon name="bootstrapXCircle" size="14" /> Reset
              </button>
            </div>

          </div>
        </div>
      </div>

      <!-- ngx-datatable -->
      <div class="card shadow-sm">
        <div class="card-body p-0">
          <ngx-datatable
            class="bootstrap ngx-datatable-custom"
            [rows]="users()"
            [columns]="columns"
            [columnMode]="ColumnMode.force"
            [rowHeight]="56"
            [headerHeight]="48"
            [footerHeight]="56"
            [externalPaging]="true"
            [count]="total()"
            [offset]="page() - 1"
            [limit]="pageSize"
            (page)="onPageChange($event)"
            [loadingIndicator]="isLoading()"
            [reorderable]="false"
            [scrollbarH]="true">

            <!-- User column -->
            <ngx-datatable-column name="User" prop="name" [sortable]="false">
              <ng-template ngx-datatable-cell-template let-row="row">
                <div class="d-flex align-items-center gap-2">
                  <div class="user-avatar-sm" [style.background]="getAvatarColor(row.role)">
                    {{ row.name?.[0]?.toUpperCase() }}
                  </div>
                  <div>
                    <div class="fw-semibold text-dark fs-sm">{{ row.name }}</div>
                    @if (row.parlor_name) {
                      <small class="text-muted">{{ row.parlor_name }}</small>
                    }
                  </div>
                </div>
              </ng-template>
            </ngx-datatable-column>

            <!-- Contact column -->
            <ngx-datatable-column name="Contact" [sortable]="false">
              <ng-template ngx-datatable-cell-template let-row="row">
                <div class="fs-sm">{{ row.phone }}</div>
                <small class="text-muted">{{ row.email }}</small>
              </ng-template>
            </ngx-datatable-column>

            <!-- Role column -->
            <ngx-datatable-column name="Role" prop="role" [sortable]="false" [width]="130">
              <ng-template ngx-datatable-cell-template let-value="value">
                <span class="badge" [class]="getRoleBadgeClass(value)">
                  {{ value | titlecase }}
                </span>
              </ng-template>
            </ngx-datatable-column>

            <!-- Status column -->
            <ngx-datatable-column name="Status" prop="is_active" [sortable]="false" [width]="110">
              <ng-template ngx-datatable-cell-template let-value="value">
                <app-status-badge [status]="value ? 'active' : 'banned'" />
              </ng-template>
            </ngx-datatable-column>

            <!-- Joined column -->
            <ngx-datatable-column name="Joined" prop="created_at" [sortable]="false" [width]="120">
              <ng-template ngx-datatable-cell-template let-value="value">
                <span class="text-muted fs-sm">{{ value | dateFormat }}</span>
              </ng-template>
            </ngx-datatable-column>

            <!-- Actions column -->
            <ngx-datatable-column name="Actions" [sortable]="false" [width]="130">
              <ng-template ngx-datatable-cell-template let-row="row">
                <div class="dropdown">
                  <button class="btn btn-sm btn-outline-secondary dropdown-toggle"
                    data-bs-toggle="dropdown">
                    Actions
                  </button>
                  <ul class="dropdown-menu dropdown-menu-end shadow-sm">
                    <li>
                      <a class="dropdown-item" [routerLink]="['/users', row.id]">
                        <ng-icon name="bootstrapEye" size="14" /> View Details
                      </a>
                    </li>
                    <li><hr class="dropdown-divider"></li>
                    @if (row.is_active) {
                      <li>
                        <a class="dropdown-item text-warning" (click)="banUser(row)" href="javascript:void(0)">
                          <ng-icon name="bootstrapSlashCircle" size="14" /> Ban User
                        </a>
                      </li>
                    } @else {
                      <li>
                        <a class="dropdown-item text-success" (click)="unbanUser(row)" href="javascript:void(0)">
                          <ng-icon name="bootstrapCheckCircle" size="14" /> Unban User
                        </a>
                      </li>
                    }
                    @if (authService.isSuperAdmin()) {
                      <li>
                        <a class="dropdown-item" (click)="changeRole(row)" href="javascript:void(0)">
                          <ng-icon name="bootstrapPersonGear" size="14" /> Change Role
                        </a>
                      </li>
                    }
                    <li><hr class="dropdown-divider"></li>
                    <li>
                      <a class="dropdown-item text-danger" (click)="deleteUser(row)" href="javascript:void(0)">
                        <ng-icon name="bootstrapTrash" size="14" /> Delete
                      </a>
                    </li>
                  </ul>
                </div>
              </ng-template>
            </ngx-datatable-column>

          </ngx-datatable>
        </div>
      </div>

    </div>
  `,
  styles: [`
    .page-title { font-size: 22px; font-weight: 700; color: #5e5873; margin-bottom: 4px; }
    .user-avatar-sm {
      width: 34px; height: 34px; border-radius: 50%;
      display: flex; align-items: center; justify-content: center;
      color: #fff; font-weight: 700; font-size: 13px; flex-shrink: 0;
    }
    .fs-sm { font-size: 13px; }
    ::ng-deep .ngx-datatable-custom .datatable-header { background: #f8f9fa; border-bottom: 2px solid #dee2e6; }
    ::ng-deep .ngx-datatable-custom .datatable-header-cell { font-size: 11px; font-weight: 700; text-transform: uppercase; color: #6e6b7b; letter-spacing: 0.04em; }
    ::ng-deep .ngx-datatable-custom .datatable-body-row:hover { background: rgba(115,103,240,0.04); }
    ::ng-deep .ngx-datatable-custom .datatable-footer { background: #f8f9fa; border-top: 1px solid #dee2e6; }
  `],
})
export class UsersListComponent implements OnInit {
  private api = inject(AdminApiService);
  protected authService = inject(AuthService);
  private toastr = inject(ToastrService);
  private searchSubject = new Subject<string>();
  private destroyRef = inject(DestroyRef);

  // State signals
  users      = signal<User[]>([]);
  total      = signal(0);
  page       = signal(1);
  isLoading  = signal(false);

  // Filters
  searchTerm   = '';
  roleFilter   = '';
  statusFilter = '';
  pageSize     = 20;

  protected ColumnMode = ColumnMode;

  ngOnInit() {
    this.loadUsers();
    this.searchSubject.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe(() => { this.page.set(1); this.loadUsers(); });
  }

  loadUsers() {
    this.isLoading.set(true);
    const params: Record<string, unknown> = {
      page: this.page(),
      limit: this.pageSize,
      ...(this.searchTerm ? { search: this.searchTerm } : {}),
      ...(this.roleFilter ? { role: this.roleFilter } : {}),
      ...(this.statusFilter !== '' ? { is_active: this.statusFilter } : {}),
    };
    this.api.getUsers(params).subscribe({
      next: (data) => { this.users.set(data.items); this.total.set(data.total); this.isLoading.set(false); },
      error: () => { this.toastr.error('Failed to load users'); this.isLoading.set(false); },
    });
  }

  onSearchChange(term: string) { this.searchSubject.next(term); }
  onPageChange(event: { offset: number }) { this.page.set(event.offset + 1); this.loadUsers(); }
  resetFilters() { this.searchTerm = ''; this.roleFilter = ''; this.statusFilter = ''; this.page.set(1); this.loadUsers(); }

  async banUser(user: User) {
    const result = await Swal.fire({
      title: 'Ban User',
      text: `Ban "${user.name}"? They will not be able to login.`,
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#ea5455',
      confirmButtonText: 'Yes, Ban',
    });
    if (result.isConfirmed) {
      this.api.updateUser(user.id, { is_active: false }).subscribe({
        next: () => { this.toastr.success(`${user.name} has been banned`); this.loadUsers(); },
        error: () => this.toastr.error('Failed to ban user'),
      });
    }
  }

  unbanUser(user: User) {
    this.api.updateUser(user.id, { is_active: true }).subscribe({
      next: () => { this.toastr.success(`${user.name} has been unbanned`); this.loadUsers(); },
      error: () => this.toastr.error('Failed to unban user'),
    });
  }

  async deleteUser(user: User) {
    const result = await Swal.fire({
      title: 'Delete User',
      html: `<strong>Permanently delete "${user.name}"?</strong><br><small class="text-muted">This cannot be undone.</small>`,
      icon: 'error',
      showCancelButton: true,
      confirmButtonColor: '#ea5455',
      confirmButtonText: 'Delete',
    });
    if (result.isConfirmed) {
      this.api.deleteUser(user.id).subscribe({
        next: () => { this.toastr.success('User deleted'); this.loadUsers(); },
        error: () => this.toastr.error('Failed to delete user'),
      });
    }
  }

  async changeRole(user: User) {
    const { value: newRole } = await Swal.fire({
      title: `Change role for ${user.name}`,
      input: 'select',
      inputOptions: { user: 'User', parlor_owner: 'Parlor Owner', admin: 'Admin', super_admin: 'Super Admin' },
      inputValue: user.role,
      showCancelButton: true,
      confirmButtonColor: '#7367f0',
    });
    if (newRole) {
      this.api.updateUser(user.id, { role: newRole }).subscribe({
        next: () => { this.toastr.success(`Role updated to ${newRole}`); this.loadUsers(); },
        error: () => this.toastr.error('Failed to update role'),
      });
    }
  }

  getRoleBadgeClass(role: string): string {
    const map: Record<string, string> = {
      super_admin: 'bg-danger', admin: 'bg-primary',
      parlor_owner: 'bg-info text-dark', user: 'bg-secondary',
    };
    return map[role] ?? 'bg-secondary';
  }

  getAvatarColor(role: string): string {
    const map: Record<string, string> = {
      super_admin: '#ea5455', admin: '#7367f0',
      parlor_owner: '#00cfe8', user: '#28c76f',
    };
    return map[role] ?? '#6c757d';
  }
}
