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
import { NgIcon, provideIcons } from '@ng-icons/core';
import { bootstrapCalendar3, bootstrapClock, bootstrapShop } from '@ng-icons/bootstrap-icons';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';

import { GamingSlot, Parlor } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { StatusBadgeComponent } from '../../shared/components/status-badge/status-badge.component';
import { CurrencyInPipe } from '../../shared/pipes/currency-in.pipe';

@Component({
  selector: 'app-slots-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    NgxDatatableModule,
    NgIcon,
    PageHeaderComponent,
    StatusBadgeComponent,
    CurrencyInPipe,
  ],
  providers: [provideIcons({ bootstrapCalendar3, bootstrapClock, bootstrapShop })],
  template: `
    <div class="slots-page">
      <app-page-header
        title="Gaming Slots"
        subtitle="Manage parlor time slots and availability"
        [breadcrumbs]="[{ label: 'Home', route: '/dashboard' }, { label: 'Slots' }]" />

      <div class="card filters-card mb-4">
        <div class="card-body">
          <div class="row g-3 align-items-end">
            <div class="col-md-4">
              <label class="form-label small text-muted mb-1">Date</label>
              <div class="input-group">
                <span class="input-group-text bg-white border-end-0">
                  <ng-icon name="bootstrapCalendar3" size="16" class="text-muted" />
                </span>
                <input
                  type="date"
                  class="form-control border-start-0"
                  [ngModel]="dateFilter()"
                  (ngModelChange)="onDateChange($event)" />
              </div>
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted mb-1">Parlor</label>
              <select
                class="form-select"
                [ngModel]="parlorFilter()"
                (ngModelChange)="onParlorChange($event)">
                <option value="">All Parlors</option>
                @for (p of parlors(); track p.id) {
                  <option [value]="p.id">{{ p.name }}</option>
                }
              </select>
            </div>
            <div class="col-md-4 text-md-end">
              <span class="badge bg-light text-dark results-badge">
                {{ total() }} slot{{ total() === 1 ? '' : 's' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="card table-card">
        <div class="card-body p-0">
          @if (loadError()) {
            <div class="error-state">
              <p class="mb-2">Failed to load slots.</p>
              <button type="button" class="btn btn-sm btn-primary" (click)="loadSlots()">Retry</button>
            </div>
          } @else {
            <ngx-datatable
              class="bootstrap slots-table"
              [rows]="rows()"
              [columnMode]="ColumnMode.force"
              [headerHeight]="48"
              [rowHeight]="60"
              [footerHeight]="56"
              [externalPaging]="true"
              [count]="total()"
              [offset]="page() - 1"
              [limit]="pageSize()"
              [scrollbarH]="true"
              [loadingIndicator]="loading()"
              (page)="onPage($event)">
              <ngx-datatable-column name="Parlor" [flexGrow]="2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="d-flex align-items-center gap-2">
                    <ng-icon name="bootstrapShop" size="16" class="text-muted" />
                    <span class="fw-medium">{{ row.parlor?.name || '—' }}</span>
                  </div>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Date" prop="slot_date" [flexGrow]="1.2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.slot_date }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Time" [flexGrow]="1.5" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="d-flex align-items-center gap-1">
                    <ng-icon name="bootstrapClock" size="14" class="text-muted" />
                    {{ row.start_time }} – {{ row.end_time }}
                  </div>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Game" prop="game" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.game || '—' }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Price/hr" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="fw-medium">{{ row.price_per_hour | currencyIn }}</span>
                  @if (row.original_price && row.original_price > row.price_per_hour) {
                    <small class="text-muted text-decoration-line-through ms-1">
                      {{ row.original_price | currencyIn }}
                    </small>
                  }
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Capacity" [flexGrow]="1.2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="capacity-cell">
                    <div class="progress mini-progress">
                      <div
                        class="progress-bar"
                        role="progressbar"
                        [style.width.%]="capacityPercent(row)"
                        [attr.aria-valuenow]="row.current_bookings"
                        aria-valuemin="0"
                        [attr.aria-valuemax]="row.max_players">
                      </div>
                    </div>
                    <span class="capacity-label">{{ row.current_bookings }}/{{ row.max_players }}</span>
                  </div>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Status" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <app-status-badge [status]="row.is_available ? 'open' : 'full'" />
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
              <div class="empty-state">No slots found for selected filters</div>
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

    .capacity-cell {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .mini-progress {
      flex: 1;
      height: 6px;
      background: #f3f2f7;
      border-radius: 3px;
    }

    .mini-progress .progress-bar {
      background: linear-gradient(90deg, #7367f0, rgba(115, 103, 240, 0.7));
      border-radius: 3px;
    }

    .capacity-label {
      font-weight: 600;
      font-size: 0.8125rem;
      min-width: 2.5rem;
      text-align: right;
      font-variant-numeric: tabular-nums;
    }

    .datatable-footer-inner {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 1rem;
      width: 100%;
      padding: 0.5rem 1rem;
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
export class SlotsListComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  readonly rows = signal<GamingSlot[]>([]);
  readonly parlors = signal<Parlor[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly pageSize = signal(20);
  readonly loading = signal(false);
  readonly loadError = signal(false);
  readonly dateFilter = signal('');
  readonly parlorFilter = signal('');

  readonly totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize())));

  protected readonly ColumnMode = ColumnMode;

  ngOnInit(): void {
    this.loadParlors();
    this.loadSlots();
  }

  capacityPercent(row: GamingSlot): number {
    if (!row.max_players) return 0;
    return Math.round((row.current_bookings / row.max_players) * 100);
  }

  onDateChange(value: string): void {
    this.dateFilter.set(value);
    this.page.set(1);
    this.loadSlots();
  }

  onParlorChange(value: string): void {
    this.parlorFilter.set(value);
    this.page.set(1);
    this.loadSlots();
  }

  onPage(event: { offset: number }): void {
    this.page.set(event.offset + 1);
    this.loadSlots();
  }

  setPage(nextPage: number): void {
    if (nextPage < 1 || nextPage > this.totalPages()) return;
    this.page.set(nextPage);
    this.loadSlots();
  }

  endRow(offset: number, pageSize: number, rowCount: number): number {
    return Math.min(offset * pageSize + rowCount, this.total());
  }

  loadParlors(): void {
    this.api
      .getParlors({ limit: 100 })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => this.parlors.set(res.items),
        error: () => this.parlors.set([]),
      });
  }

  loadSlots(): void {
    this.loading.set(true);
    this.loadError.set(false);

    const params: Record<string, string | number> = {
      page: this.page(),
      limit: this.pageSize(),
    };

    const date = this.dateFilter();
    if (date) params['date'] = date;

    const parlorId = this.parlorFilter();
    if (parlorId) params['parlor_id'] = parlorId;

    this.api
      .getGamingSlots(params)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.rows.set(res.items);
          this.total.set(res.total);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.loadError.set(true);
          this.toast.error('Failed to load slots');
        },
      });
  }
}