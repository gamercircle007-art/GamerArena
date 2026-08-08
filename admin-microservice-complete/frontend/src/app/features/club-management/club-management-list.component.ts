import {
  ChangeDetectionStrategy,
  Component,
  computed,
  DestroyRef,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { bootstrapBuilding, bootstrapSearch } from '@ng-icons/bootstrap-icons';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

import { hasPermission, PERMISSIONS } from '../../core/constants/permissions';
import { ClubSummary } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { TruncatePipe } from '../../shared/pipes/truncate.pipe';

@Component({
  selector: 'app-club-management-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    RouterLink,
    NgxDatatableModule,
    NgIcon,
    PageHeaderComponent,
    TruncatePipe,
  ],
  providers: [provideIcons({ bootstrapSearch, bootstrapBuilding })],
  template: `
    <div class="clubs-page" data-testid="club-management-list-page">
      <app-page-header
        title="Club Management"
        subtitle="Platform oversight for club floors, live occupancy, revenue and analytics"
        [breadcrumbs]="[{ label: 'Home', route: '/dashboard' }, { label: 'Club Management' }]">
        <button
          type="button"
          class="btn btn-sm btn-light"
          data-testid="club-list-refresh-btn"
          [disabled]="loading()"
          (click)="loadClubs()">
          Refresh
        </button>
      </app-page-header>

      @if (!canView()) {
        <div class="card">
          <div class="card-body text-center py-5 text-muted">
            You do not have permission to view club management.
          </div>
        </div>
      } @else {
        <div class="card filters-card mb-4">
          <div class="card-body">
            <div class="row g-3 align-items-end">
              <div class="col-md-6">
                <label class="form-label small text-muted mb-1">Search clubs</label>
                <div class="input-group">
                  <span class="input-group-text bg-white border-end-0">
                    <ng-icon name="bootstrapSearch" size="16" class="text-muted" />
                  </span>
                  <input
                    type="search"
                    class="form-control border-start-0 ps-0"
                    placeholder="Search by club name..."
                    data-testid="club-list-search-input"
                    [ngModel]="searchInput()"
                    (ngModelChange)="onSearchChange($event)" />
                </div>
              </div>
              <div class="col-md-6 text-md-end">
                <span class="badge bg-light text-dark results-badge">
                  {{ rows().length }} club{{ rows().length === 1 ? '' : 's' }} on this page
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="card table-card">
          <div class="card-body p-0">
            @if (loadError()) {
              <div class="error-state">
                <p class="mb-2">Failed to load clubs.</p>
                <button
                  type="button"
                  class="btn btn-sm btn-primary"
                  data-testid="club-list-retry-btn"
                  (click)="loadClubs()">
                  Retry
                </button>
              </div>
            } @else {
              <ngx-datatable
                class="bootstrap clubs-table"
                data-testid="club-list-table"
                [rows]="rows()"
                [columnMode]="ColumnMode.force"
                [headerHeight]="48"
                [rowHeight]="60"
                [footerHeight]="0"
                [scrollbarH]="true"
                [loadingIndicator]="loading()"
                (activate)="onActivate($event)">
                <ngx-datatable-column name="Club" prop="name" [flexGrow]="3" [sortable]="true">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    <div class="d-flex align-items-center gap-2">
                      <div class="club-logo">
                        <ng-icon name="bootstrapBuilding" size="16" />
                      </div>
                      <div class="min-w-0">
                        <span class="fw-medium text-dark d-block text-truncate">{{ row.name }}</span>
                        <small class="text-muted d-block">{{ row.parlor_id | truncate: 12 }}</small>
                      </div>
                    </div>
                  </ng-template>
                </ngx-datatable-column>

                <ngx-datatable-column name="Owner" prop="owner_id" [flexGrow]="2" [sortable]="false">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    @if (row.owner_id) {
                      <a
                        class="owner-link"
                        [routerLink]="['/users', row.owner_id]"
                        data-testid="club-list-owner-link">
                        {{ row.owner_id | truncate: 14 }}
                      </a>
                    } @else {
                      <span class="text-muted">— unassigned</span>
                    }
                  </ng-template>
                </ngx-datatable-column>

                <ngx-datatable-column
                  name="Oversight"
                  [flexGrow]="1.2"
                  [sortable]="false"
                  [resizeable]="false">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    <a
                      class="btn btn-sm btn-outline-primary"
                      data-testid="club-list-open-btn"
                      [routerLink]="['/club-management', row.parlor_id]">
                      Open
                    </a>
                  </ng-template>
                </ngx-datatable-column>
              </ngx-datatable>

              @if (!loading() && !rows().length) {
                <div class="empty-state">No clubs found</div>
              }

              <div class="table-pager">
                <button
                  type="button"
                  class="btn btn-sm btn-outline-secondary"
                  data-testid="club-list-prev-btn"
                  [disabled]="offset() === 0 || loading()"
                  (click)="prevPage()">
                  Prev
                </button>
                <span class="small text-muted">
                  Showing {{ offset() + 1 }}–{{ offset() + rows().length }}
                </span>
                <button
                  type="button"
                  class="btn btn-sm btn-outline-secondary"
                  data-testid="club-list-next-btn"
                  [disabled]="rows().length < pageSize() || loading()"
                  (click)="nextPage()">
                  Next
                </button>
              </div>
            }
          </div>
        </div>
      }
    </div>
  `,
  styles: `
    .filters-card .card-body { padding: 1.25rem 1.5rem; }

    .results-badge {
      font-size: 0.8125rem;
      font-weight: 600;
      padding: 0.5rem 0.75rem;
      border: 1px solid #ebe9f1;
    }

    .clubs-table { box-shadow: none; }

    :host ::ng-deep .clubs-table .datatable-body-row { cursor: pointer; }

    .club-logo {
      width: 32px;
      height: 32px;
      border-radius: 0.5rem;
      background: #f3f2f7;
      color: #7367f0;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .owner-link {
      font-size: 0.8125rem;
      color: #7367f0;
      text-decoration: none;
    }

    .owner-link:hover { text-decoration: underline; }

    .table-pager {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 1rem;
      padding: 0.75rem 1rem;
      border-top: 1px solid #ebe9f1;
    }

    .empty-state,
    .error-state {
      padding: 2.5rem 1rem;
      text-align: center;
      color: #b9b9c3;
      font-size: 0.875rem;
    }
  `,
})
export class ClubManagementListComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly auth = inject(AuthService);
  private readonly toast = inject(ToastService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  private readonly searchSubject = new Subject<string>();

  readonly rows = signal<ClubSummary[]>([]);
  readonly loading = signal(false);
  readonly loadError = signal(false);
  readonly searchInput = signal('');
  readonly offset = signal(0);
  readonly pageSize = signal(20);

  protected readonly ColumnMode = ColumnMode;

  readonly canView = computed(() => {
    const role = this.auth.currentUser()?.role;
    return role ? hasPermission(role, PERMISSIONS.VIEW_CLUB_MANAGEMENT) : false;
  });

  ngOnInit(): void {
    this.searchSubject
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe(term => {
        this.searchInput.set(term);
        this.offset.set(0);
        this.loadClubs();
      });

    if (this.canView()) {
      this.loadClubs();
    }
  }

  onSearchChange(value: string): void {
    this.searchSubject.next(value);
  }

  onActivate(event: { type: string; row: ClubSummary }): void {
    if (event.type !== 'click' || !event.row) return;
    this.router.navigate(['/club-management', event.row.parlor_id]);
  }

  prevPage(): void {
    const next = Math.max(0, this.offset() - this.pageSize());
    if (next === this.offset()) return;
    this.offset.set(next);
    this.loadClubs();
  }

  nextPage(): void {
    if (this.rows().length < this.pageSize()) return;
    this.offset.set(this.offset() + this.pageSize());
    this.loadClubs();
  }

  loadClubs(): void {
    this.loading.set(true);
    this.loadError.set(false);

    const search = this.searchInput().trim();

    this.api
      .getClubManagementClubs({
        limit: this.pageSize(),
        offset: this.offset(),
        ...(search ? { search } : {}),
      })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.rows.set(res.items ?? []);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.loadError.set(true);
          this.toast.error('Failed to load clubs');
        },
      });
  }
}
