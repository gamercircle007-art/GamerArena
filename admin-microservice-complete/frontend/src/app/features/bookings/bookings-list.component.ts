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
import {
  bootstrapArrowRepeat,
  bootstrapCalendar3,
  bootstrapCurrencyRupee,
  bootstrapPerson,
  bootstrapTicketPerforated,
} from '@ng-icons/bootstrap-icons';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';

import { Booking, GamingBooking } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { ToastService } from '../../core/services/toast.service';
import { BookingStatusBadgeComponent } from '../../shared/components/booking-status-badge/booking-status-badge.component';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { CurrencyInPipe } from '../../shared/pipes/currency-in.pipe';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';
import { ConfirmService } from '../../shared/services/confirm.service';

type BookingTab = 'tournament' | 'slot' | 'refunds';
type StatusFilter = '' | 'confirmed' | 'pending' | 'cancelled';

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: '', label: 'All Status' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'pending', label: 'Pending' },
  { value: 'cancelled', label: 'Cancelled' },
];

@Component({
  selector: 'app-bookings-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    NgxDatatableModule,
    NgIcon,
    PageHeaderComponent,
    BookingStatusBadgeComponent,
    DateFormatPipe,
    CurrencyInPipe,
  ],
  providers: [
    provideIcons({
      bootstrapPerson,
      bootstrapTicketPerforated,
      bootstrapCalendar3,
      bootstrapCurrencyRupee,
      bootstrapArrowRepeat,
    }),
  ],
  template: `
    <div class="bookings-page">
      <app-page-header
        title="Bookings"
        subtitle="View tournament, slot, and refund bookings"
        [breadcrumbs]="[
          { label: 'Home', route: '/dashboard' },
          { label: 'Bookings' },
        ]">
        <div class="revenue-header d-flex align-items-center gap-2">
          <ng-icon name="bootstrapCurrencyRupee" size="18" class="text-warning" />
          <div>
            <small class="text-muted d-block">Revenue (filtered)</small>
            <span class="fw-bold revenue-value">{{ revenueTotal() | currencyIn }}</span>
          </div>
        </div>
      </app-page-header>

      <ul class="nav nav-tabs booking-tabs mb-4">
        <li class="nav-item">
          <button
            type="button"
            class="nav-link"
            [class.active]="activeTab() === 'tournament'"
            (click)="setTab('tournament')">
            <ng-icon name="bootstrapTicketPerforated" size="16" class="me-1" />
            Tournament Bookings
          </button>
        </li>
        <li class="nav-item">
          <button
            type="button"
            class="nav-link"
            [class.active]="activeTab() === 'slot'"
            (click)="setTab('slot')">
            <ng-icon name="bootstrapTicketPerforated" size="16" class="me-1" />
            Time Slot Bookings
          </button>
        </li>
        <li class="nav-item">
          <button
            type="button"
            class="nav-link"
            [class.active]="activeTab() === 'refunds'"
            (click)="setTab('refunds')">
            <ng-icon name="bootstrapArrowRepeat" size="16" class="me-1" />
            Pending Refunds
            @if (pendingRefundCount() > 0) {
              <span class="badge bg-warning text-dark ms-1">{{ pendingRefundCount() }}</span>
            }
          </button>
        </li>
      </ul>

      <div class="card filters-card mb-4">
        <div class="card-body">
          <div class="row g-3 align-items-end">
            @if (activeTab() !== 'refunds') {
              <div class="col-md-3">
                <label class="form-label small text-muted mb-1">Status</label>
                <select
                  class="form-select"
                  [ngModel]="statusFilter()"
                  (ngModelChange)="onStatusChange($event)">
                  @for (opt of statusOptions; track opt.value) {
                    <option [value]="opt.value">{{ opt.label }}</option>
                  }
                </select>
              </div>
            }
            <div class="col-md-3">
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
            <div class="col-md text-md-end">
              <span class="badge bg-light text-dark results-badge">
                {{ total() }} booking{{ total() === 1 ? '' : 's' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="card table-card">
        <div class="card-body p-0">
          @if (loadError()) {
            <div class="error-state">
              <p class="mb-2">Failed to load bookings.</p>
              <button type="button" class="btn btn-sm btn-primary" (click)="loadBookings()">
                Retry
              </button>
            </div>
          } @else if (activeTab() === 'refunds') {
            <ngx-datatable
              class="bootstrap bookings-table"
              [rows]="gamingRows()"
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
              (page)="onPage($event)">
              <ngx-datatable-column name="Ref" prop="booking_ref" [flexGrow]="1.2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="fw-medium font-monospace small">{{ row.booking_ref }}</span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="User" [flexGrow]="1.5" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="d-flex align-items-center gap-2">
                    <ng-icon name="bootstrapPerson" size="16" class="text-muted" />
                    <span class="fw-medium">{{ gamingUserName(row) }}</span>
                  </div>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Parlor" [flexGrow]="1.5" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.parlor?.name || '—' }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Slot Date" [flexGrow]="1.2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.slot_date || '—' }}
                  @if (row.start_time) {
                    <small class="text-muted d-block">{{ row.start_time }} – {{ row.end_time }}</small>
                  }
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Refund" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="fw-semibold text-danger">{{ row.refund_amount | currencyIn }}</span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Status" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <app-booking-status-badge [status]="row.refund_status || 'refund_pending'" />
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Actions" [flexGrow]="1.2" [sortable]="false" [resizeable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <button
                    type="button"
                    class="btn btn-sm btn-primary"
                    [disabled]="actionId() === row.id"
                    (click)="processRefund(row)">
                    Process Refund
                  </button>
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

            @if (!loading() && !gamingRows().length) {
              <div class="empty-state">No pending refunds</div>
            }
          } @else {
            <ngx-datatable
              class="bootstrap bookings-table"
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
              (page)="onPage($event)">
              <ngx-datatable-column name="User" [flexGrow]="2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="d-flex align-items-center gap-2">
                    <ng-icon name="bootstrapPerson" size="16" class="text-muted" />
                    <span class="fw-medium">{{ userName(row) }}</span>
                  </div>
                </ng-template>
              </ngx-datatable-column>

              @if (activeTab() === 'tournament') {
                <ngx-datatable-column name="Tournament" [flexGrow]="2" [sortable]="false">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    {{ row.tournament?.title || '—' }}
                  </ng-template>
                </ngx-datatable-column>

                <ngx-datatable-column name="Parlor" [flexGrow]="1.5" [sortable]="false">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    {{ row.tournament?.parlor?.name || '—' }}
                  </ng-template>
                </ngx-datatable-column>

                <ngx-datatable-column name="Game" [flexGrow]="1" [sortable]="false">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    {{ row.tournament?.game_type || '—' }}
                  </ng-template>
                </ngx-datatable-column>
              } @else {
                <ngx-datatable-column name="Slot" [flexGrow]="2" [sortable]="false">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    {{ row.tournament?.title || '—' }}
                  </ng-template>
                </ngx-datatable-column>

                <ngx-datatable-column name="Parlor" [flexGrow]="1.5" [sortable]="false">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    {{ row.tournament?.parlor?.name || '—' }}
                  </ng-template>
                </ngx-datatable-column>

                <ngx-datatable-column name="Slot #" prop="slot_number" [flexGrow]="0.8" [sortable]="false">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    #{{ row.slot_number }}
                  </ng-template>
                </ngx-datatable-column>
              }

              <ngx-datatable-column name="Entry Fee" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.tournament?.entry_fee | currencyIn }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Payment" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <app-booking-status-badge [status]="row.payment_status" />
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Status" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <app-booking-status-badge [status]="row.status" />
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Booked" prop="created_at" [flexGrow]="1.3" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.created_at | dateFormat }}
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
              <div class="empty-state">No bookings found</div>
            }
          }
        </div>
      </div>
    </div>
  `,
  styles: `
    .booking-tabs .nav-link {
      border: none;
      color: #6e6b7b;
      font-weight: 500;
      padding: 0.75rem 1.25rem;
      cursor: pointer;
      background: transparent;
    }

    .booking-tabs .nav-link.active {
      color: #7367f0;
      border-bottom: 2px solid #7367f0;
    }

    .revenue-header {
      background: #fff8e1;
      border: 1px solid #ffe082;
      border-radius: 8px;
      padding: 0.5rem 1rem;
    }

    .revenue-value {
      font-size: 1.125rem;
      color: #ff9f43;
      font-variant-numeric: tabular-nums;
    }

    .filters-card .card-body { padding: 1.25rem 1.5rem; }

    .results-badge {
      font-size: 0.8125rem;
      font-weight: 600;
      padding: 0.5rem 0.75rem;
      border: 1px solid #ebe9f1;
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
export class BookingsListComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly destroyRef = inject(DestroyRef);

  readonly rows = signal<Booking[]>([]);
  readonly gamingRows = signal<GamingBooking[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly pageSize = signal(20);
  readonly loading = signal(false);
  readonly loadError = signal(false);
  readonly activeTab = signal<BookingTab>('tournament');
  readonly statusFilter = signal<StatusFilter>('');
  readonly dateFilter = signal('');
  readonly actionId = signal<string | null>(null);
  readonly pendingRefundCount = signal(0);

  readonly statusOptions = STATUS_OPTIONS;
  readonly totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize())));

  readonly revenueTotal = computed(() => {
    if (this.activeTab() === 'refunds') {
      return this.gamingRows().reduce((sum, row) => sum + (row.refund_amount ?? 0), 0);
    }
    return this.rows().reduce(
      (sum, row) => sum + (row.tournament?.entry_fee ?? 0),
      0,
    );
  });

  protected readonly ColumnMode = ColumnMode;

  ngOnInit(): void {
    this.loadPendingRefundCount();
    this.loadBookings();
  }

  userName(row: Booking): string {
    return row.user?.name ?? row.user?.username ?? 'Unknown User';
  }

  gamingUserName(row: GamingBooking): string {
    return row.user?.name ?? row.user?.username ?? row.guest_name ?? 'Unknown User';
  }

  setTab(tab: BookingTab): void {
    this.activeTab.set(tab);
    this.page.set(1);
    this.loadBookings();
  }

  onStatusChange(value: StatusFilter): void {
    this.statusFilter.set(value);
    this.page.set(1);
    this.loadBookings();
  }

  onDateChange(value: string): void {
    this.dateFilter.set(value);
    this.page.set(1);
    this.loadBookings();
  }

  onPage(event: { offset: number }): void {
    this.page.set(event.offset + 1);
    this.loadBookings();
  }

  setPage(nextPage: number): void {
    if (nextPage < 1 || nextPage > this.totalPages()) return;
    this.page.set(nextPage);
    this.loadBookings();
  }

  endRow(offset: number, pageSize: number, rowCount: number): number {
    return Math.min(offset * pageSize + rowCount, this.total());
  }

  async processRefund(row: GamingBooking): Promise<void> {
    const confirmed = await this.confirm.confirm(
      'Process Refund',
      `Process refund of ${row.refund_amount} for ${row.booking_ref}?`,
      'Process',
      'question',
    );
    if (!confirmed) return;

    this.actionId.set(row.id);
    this.api
      .processGamingRefund(row.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionId.set(null);
          this.toast.success('Refund processed successfully');
          this.loadPendingRefundCount();
          this.loadBookings();
        },
        error: () => {
          this.actionId.set(null);
          this.toast.error('Failed to process refund');
        },
      });
  }

  loadPendingRefundCount(): void {
    this.api
      .getGamingBookings({ refund_status: 'pending', limit: 1 })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => this.pendingRefundCount.set(res.total),
        error: () => this.pendingRefundCount.set(0),
      });
  }

  loadBookings(): void {
    this.loading.set(true);
    this.loadError.set(false);

    if (this.activeTab() === 'refunds') {
      const params: Record<string, string | number> = {
        page: this.page(),
        limit: this.pageSize(),
        refund_status: 'pending',
      };
      const date = this.dateFilter();
      if (date) params['date'] = date;

      this.api
        .getGamingBookings(params)
        .pipe(takeUntilDestroyed(this.destroyRef))
        .subscribe({
          next: res => {
            this.gamingRows.set(res.items);
            this.total.set(res.total);
            this.loading.set(false);
          },
          error: () => {
            this.loading.set(false);
            this.loadError.set(true);
            this.toast.error('Failed to load pending refunds');
          },
        });
      return;
    }

    const params: Record<string, string | number> = {
      page: this.page(),
      limit: this.pageSize(),
      booking_type: this.activeTab(),
    };

    const status = this.statusFilter();
    if (status) params['status'] = status;

    const date = this.dateFilter();
    if (date) params['date'] = date;

    this.api
      .getBookings(params)
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
          this.toast.error('Failed to load bookings');
        },
      });
  }
}