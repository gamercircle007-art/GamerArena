import { DecimalPipe } from '@angular/common';
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
import { ActivatedRoute, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  bootstrapCheckCircle,
  bootstrapSearch,
  bootstrapShop,
  bootstrapStarFill,
  bootstrapThreeDotsVertical,
} from '@ng-icons/bootstrap-icons';
import { BsDropdownModule } from 'ngx-bootstrap/dropdown';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

import { hasPermission, PERMISSIONS } from '../../core/constants/permissions';
import { Parlor } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { AuthService } from '../../core/services/auth.service';
import { MockDataService } from '../../core/services/mock-data.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { StatusBadgeComponent } from '../../shared/components/status-badge/status-badge.component';
import { ConfirmService } from '../../shared/services/confirm.service';

type VerifiedFilter = '' | 'verified' | 'pending';

@Component({
  selector: 'app-parlors-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DecimalPipe,
    FormsModule,
    RouterLink,
    NgxDatatableModule,
    BsDropdownModule,
    NgIcon,
    PageHeaderComponent,
    StatusBadgeComponent,
  ],
  providers: [
    provideIcons({
      bootstrapSearch,
      bootstrapShop,
      bootstrapStarFill,
      bootstrapCheckCircle,
      bootstrapThreeDotsVertical,
    }),
  ],
  template: `
    <div class="parlors-page">
      <app-page-header
        title="Parlors"
        subtitle="Create, review, verify, and manage gaming parlors"
        [breadcrumbs]="[{ label: 'Home', route: '/dashboard' }, { label: 'Parlors' }]">
        @if (canManage()) {
          <a routerLink="/parlors/new" class="btn btn-sm btn-primary">+ Create Parlor</a>
        }
      </app-page-header>

      <div class="card filters-card mb-4">
        <div class="card-body">
          <div class="row g-3 align-items-end">
            <div class="col-md-5">
              <label class="form-label small text-muted mb-1">Search</label>
              <div class="input-group">
                <span class="input-group-text bg-white border-end-0">
                  <ng-icon name="bootstrapSearch" size="16" class="text-muted" />
                </span>
                <input
                  type="search"
                  class="form-control border-start-0 ps-0"
                  placeholder="Search name, address, games..."
                  [ngModel]="searchInput()"
                  (ngModelChange)="onSearchChange($event)" />
              </div>
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted mb-1">Verification</label>
              <select
                class="form-select"
                [ngModel]="verifiedFilter()"
                (ngModelChange)="onVerifiedChange($event)">
                <option value="">All Parlors</option>
                <option value="verified">Verified</option>
                <option value="pending">Pending Verification</option>
              </select>
            </div>
            <div class="col-md-3 text-md-end">
              <span class="badge bg-light text-dark results-badge">
                {{ total() }} parlor{{ total() === 1 ? '' : 's' }}
              </span>
              @if (pendingCount() > 0) {
                <span class="badge bg-warning-subtle text-warning ms-2">
                  {{ pendingCount() }} pending
                </span>
              }
            </div>
          </div>
        </div>
      </div>

      <div class="card table-card">
        <div class="card-body p-0">
          @if (loadError()) {
            <div class="error-state">
              <p class="mb-2">Failed to load parlors.</p>
              <button type="button" class="btn btn-sm btn-primary" (click)="loadParlors()">
                Retry
              </button>
            </div>
          } @else {
            <ngx-datatable
              class="bootstrap parlors-table"
              [rows]="rows()"
              [columnMode]="ColumnMode.force"
              [headerHeight]="48"
              [rowHeight]="64"
              [footerHeight]="56"
              [externalPaging]="true"
              [count]="total()"
              [offset]="page() - 1"
              [limit]="pageSize()"
              [scrollbarH]="true"
              [loadingIndicator]="loading()"
              [rowClass]="getRowClass"
              (page)="onPage($event)"
              (sort)="onSort($event)">
              <ngx-datatable-column name="Parlor" prop="name" [flexGrow]="2.5" [sortable]="true">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="d-flex align-items-center gap-2">
                    <div class="parlor-logo">
                      @if (row.logo_url) {
                        <img [src]="row.logo_url" [alt]="row.name" />
                      } @else {
                        <ng-icon name="bootstrapShop" size="16" />
                      }
                    </div>
                    <div class="min-w-0">
                      <span class="fw-medium text-dark d-block text-truncate">{{ row.name }}</span>
                      <small class="text-muted d-block text-truncate">{{ row.address || '—' }}</small>
                    </div>
                  </div>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Owner" [flexGrow]="1.8" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  @if (ownerInfo(row); as owner) {
                    <div class="owner-cell">
                      <span>{{ owner.name }}</span>
                      <small class="text-muted d-block">{{ owner.phone || row.phone || '—' }}</small>
                    </div>
                  } @else {
                    <div class="owner-cell">
                      <span class="text-muted">—</span>
                      <small class="text-muted d-block">{{ row.phone || '—' }}</small>
                    </div>
                  }
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Games" [flexGrow]="2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="games-cell">
                    @for (game of visibleGames(row); track game) {
                      <span class="game-chip">{{ game }}</span>
                    }
                    @if (extraGamesCount(row) > 0) {
                      <span class="game-chip game-chip--more">+{{ extraGamesCount(row) }} more</span>
                    }
                    @if (!row.game_types?.length) {
                      <span class="text-muted small">—</span>
                    }
                  </div>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Rating" prop="rating" [flexGrow]="1.3" [sortable]="true">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  @if (row.rating != null) {
                    <div class="rating-cell">
                      <span class="stars">
                        @for (star of starRange(row.rating); track $index) {
                          <ng-icon
                            name="bootstrapStarFill"
                            size="12"
                            [class.star-filled]="star"
                            [class.star-empty]="!star" />
                        }
                      </span>
                      <span class="rating-value">{{ row.rating | number: '1.1-1' }}</span>
                      <small class="text-muted">({{ row.post_count }} posts)</small>
                    </div>
                  } @else {
                    <span class="text-muted">—</span>
                  }
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column
                name="Followers"
                prop="follower_count"
                [flexGrow]="1"
                [sortable]="true">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ formatCount(row.follower_count) }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Status" prop="is_verified" [flexGrow]="1.1" [sortable]="true">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  @if (row.is_verified) {
                    <span class="verified-badge">
                      <ng-icon name="bootstrapCheckCircle" size="14" />
                      Verified
                    </span>
                  } @else {
                    <app-status-badge status="pending" />
                  }
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Actions" [flexGrow]="1" [sortable]="false" [resizeable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="dropdown" dropdown container="body" [dropup]="true">
                    <button
                      type="button"
                      class="btn btn-sm btn-light actions-btn"
                      dropdownToggle
                      aria-label="Parlor actions">
                      <ng-icon name="bootstrapThreeDotsVertical" size="16" />
                    </button>
                    <ul *dropdownMenu class="dropdown-menu dropdown-menu-end shadow-sm">
                      @if (canVerify() && !row.is_verified) {
                        <li>
                          <button
                            type="button"
                            class="dropdown-item text-success"
                            [disabled]="actionParlorId() === row.id"
                            (click)="verifyParlor(row, true)">
                            Verify
                          </button>
                        </li>
                      }
                      @if (canVerify() && row.is_verified) {
                        <li>
                          <button
                            type="button"
                            class="dropdown-item text-warning"
                            [disabled]="actionParlorId() === row.id"
                            (click)="verifyParlor(row, false)">
                            Unverify
                          </button>
                        </li>
                      }
                      <li>
                        <a class="dropdown-item" [routerLink]="['/parlors', row.id]">View Detail</a>
                      </li>
                      @if (canManage()) {
                        <li>
                          <a class="dropdown-item" [routerLink]="['/parlors', row.id, 'edit']">Edit</a>
                        </li>
                      }
                      @if (canDelete()) {
                        <li><hr class="dropdown-divider" /></li>
                        <li>
                          <button
                            type="button"
                            class="dropdown-item text-danger"
                            [disabled]="actionParlorId() === row.id"
                            (click)="deleteParlor(row)">
                            Soft Delete
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
              <div class="empty-state">No parlors found</div>
            }
          }
        </div>
      </div>
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

    .parlors-table { box-shadow: none; }

    :host ::ng-deep .parlors-table .datatable-body-row.row-unverified .datatable-body-cell:first-child {
      box-shadow: inset 3px 0 0 #ff9f43;
    }

    .parlor-logo {
      width: 32px;
      height: 32px;
      border-radius: 0.5rem;
      background: #f3f2f7;
      color: #7367f0;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      overflow: hidden;
    }

    .parlor-logo img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .owner-cell { font-size: 0.875rem; line-height: 1.35; }

    .games-cell {
      display: flex;
      flex-wrap: wrap;
      gap: 0.25rem;
    }

    .game-chip {
      display: inline-block;
      padding: 0.125rem 0.5rem;
      border-radius: 0.25rem;
      font-size: 0.6875rem;
      font-weight: 600;
      background: rgba(115, 103, 240, 0.1);
      color: #7367f0;
      white-space: nowrap;
    }

    .game-chip--more {
      background: #f3f2f7;
      color: #6e6b7b;
    }

    .rating-cell {
      display: flex;
      flex-direction: column;
      gap: 0.125rem;
      font-size: 0.8125rem;
    }

    .stars {
      display: flex;
      gap: 1px;
    }

    .star-filled { color: #ff9f43; }
    .star-empty { color: #d8d6de; }

    .rating-value { font-weight: 600; color: #5e5873; }

    .verified-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      padding: 0.25rem 0.625rem;
      border-radius: 0.375rem;
      font-size: 0.75rem;
      font-weight: 600;
      background: rgba(40, 199, 111, 0.12);
      color: #28c76f;
    }

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
  `,
})
export class ParlorsListComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly auth = inject(AuthService);
  private readonly mock = inject(MockDataService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly route = inject(ActivatedRoute);
  private readonly destroyRef = inject(DestroyRef);

  private readonly searchSubject = new Subject<string>();

  readonly rows = signal<Parlor[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly pageSize = signal(20);
  readonly loading = signal(false);
  readonly loadError = signal(false);
  readonly searchInput = signal('');
  readonly verifiedFilter = signal<VerifiedFilter>('');
  readonly actionParlorId = signal<string | null>(null);
  readonly sortProp = signal('created_at');
  readonly sortDir = signal<'asc' | 'desc'>('desc');

  readonly pageSizes = [10, 20, 50];
  readonly pendingCount = signal(0);

  protected readonly ColumnMode = ColumnMode;

  readonly totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize())));

  readonly canVerify = computed(() => {
    const role = this.auth.currentUser()?.role;
    return role ? hasPermission(role, PERMISSIONS.VERIFY_PARLORS) : false;
  });

  readonly canDelete = computed(() => {
    const role = this.auth.currentUser()?.role;
    return role ? hasPermission(role, PERMISSIONS.DELETE_PARLORS) : false;
  });

  readonly canManage = computed(() => {
    const role = this.auth.currentUser()?.role;
    return role
      ? hasPermission(role, PERMISSIONS.MANAGE_PARLORS) || hasPermission(role, PERMISSIONS.VERIFY_PARLORS)
      : false;
  });

  readonly getRowClass = (row: Parlor): Record<string, boolean> => ({
    'row-unverified': !row.is_verified,
  });

  ngOnInit(): void {
    this.route.queryParams.pipe(takeUntilDestroyed(this.destroyRef)).subscribe(params => {
      if (params['filter'] === 'unverified') {
        this.verifiedFilter.set('pending');
        this.page.set(1);
        this.loadParlors();
      }
    });

    this.searchSubject
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe(term => {
        this.searchInput.set(term);
        this.page.set(1);
        this.loadParlors();
      });

    this.loadParlors();
    this.loadPendingCount();
  }

  onSearchChange(value: string): void {
    this.searchSubject.next(value);
  }

  onVerifiedChange(value: VerifiedFilter): void {
    this.verifiedFilter.set(value);
    this.page.set(1);
    this.loadParlors();
  }

  onPageSizeChange(size: number | string): void {
    this.pageSize.set(Number(size));
    this.page.set(1);
    this.loadParlors();
  }

  onPage(event: { offset: number }): void {
    this.page.set(event.offset + 1);
    this.loadParlors();
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
    this.loadParlors();
  }

  endRow(offset: number, pageSize: number, rowCount: number): number {
    return Math.min(offset * pageSize + rowCount, this.total());
  }

  ownerInfo(parlor: Parlor): { name: string; phone: string } | null {
    return this.mock.getOwnerInfo(parlor.owner_id);
  }

  visibleGames(parlor: Parlor): string[] {
    return (parlor.game_types ?? []).slice(0, 3);
  }

  extraGamesCount(parlor: Parlor): number {
    return Math.max(0, (parlor.game_types?.length ?? 0) - 3);
  }

  starRange(rating: number): boolean[] {
    const filled = Math.round(rating);
    return Array.from({ length: 5 }, (_, i) => i < filled);
  }

  formatCount(value: number): string {
    if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
    if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
    return String(value);
  }

  verifyParlor(parlor: Parlor, isVerified: boolean): void {
    this.actionParlorId.set(parlor.id);
    this.api
      .verifyParlor(parlor.id, isVerified)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionParlorId.set(null);
          this.toast.success(isVerified ? 'Parlor verified' : 'Parlor unverified');
          this.loadParlors();
          this.loadPendingCount();
        },
        error: () => {
          this.actionParlorId.set(null);
          this.toast.error('Failed to update verification status');
        },
      });
  }

  async deleteParlor(parlor: Parlor): Promise<void> {
    const confirmed = await this.confirm.confirmDanger(
      'Soft Delete Parlor',
      `Deactivate and soft-delete "${parlor.name}"? It can be restored later.`,
    );
    if (!confirmed) return;

    this.actionParlorId.set(parlor.id);
    this.api
      .deleteParlor(parlor.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionParlorId.set(null);
          this.toast.success('Parlor deleted');
          this.loadParlors();
          this.loadPendingCount();
        },
        error: () => {
          this.actionParlorId.set(null);
          this.toast.error('Failed to delete parlor');
        },
      });
  }

  loadParlors(): void {
    this.loading.set(true);
    this.loadError.set(false);

    const params: Record<string, string | number | boolean> = {
      page: this.page(),
      limit: this.pageSize(),
    };

    const search = this.searchInput().trim();
    if (search) params['search'] = search;

    const verified = this.verifiedFilter();
    if (verified === 'verified') params['is_verified'] = true;
    if (verified === 'pending') params['is_verified'] = false;

    this.api
      .getParlors(params)
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
          this.toast.error('Failed to load parlors');
        },
      });
  }

  private loadPendingCount(): void {
    this.api
      .getParlors({ is_verified: false, page: 1, limit: 1 })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => this.pendingCount.set(res.total),
        error: () => this.pendingCount.set(0),
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

  private sortValue(parlor: Parlor, prop: string): string | number | boolean {
    if (prop === 'is_verified') return parlor.is_verified ? 1 : 0;
    if (prop === 'rating') return parlor.rating ?? 0;
    if (prop === 'follower_count') return parlor.follower_count;
    const value = parlor[prop as keyof Parlor];
    if (typeof value === 'boolean') return value ? 1 : 0;
    if (typeof value === 'number') return value;
    return String(value ?? '').toLowerCase();
  }
}