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
  bootstrapCalendarEvent,
  bootstrapImage,
  bootstrapSearch,
  bootstrapTrash,
} from '@ng-icons/bootstrap-icons';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

import { ParlourEvent } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { StatusBadgeComponent } from '../../shared/components/status-badge/status-badge.component';
import { CurrencyInPipe } from '../../shared/pipes/currency-in.pipe';
import { ConfirmService } from '../../shared/services/confirm.service';

const EVENT_STATUSES = ['open', 'live', 'completed', 'cancelled'] as const;

@Component({
  selector: 'app-events-list',
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
  providers: [
    provideIcons({
      bootstrapSearch,
      bootstrapCalendarEvent,
      bootstrapImage,
      bootstrapTrash,
    }),
  ],
  template: `
    <div class="events-page">
      <app-page-header
        title="Events"
        subtitle="Parlor events and activities"
        [breadcrumbs]="[{ label: 'Home', route: '/dashboard' }, { label: 'Events' }]" />

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
                  placeholder="Search title or parlor..."
                  [ngModel]="searchInput()"
                  (ngModelChange)="onSearchChange($event)" />
              </div>
            </div>
            <div class="col-md-4">
              <label class="form-label small text-muted mb-1">Status</label>
              <select
                class="form-select"
                [ngModel]="statusFilter()"
                (ngModelChange)="onStatusChange($event)">
                <option value="">All Status</option>
                @for (s of eventStatuses; track s) {
                  <option [value]="s">{{ s }}</option>
                }
              </select>
            </div>
            <div class="col-md-3 text-md-end">
              <span class="badge bg-light text-dark results-badge">
                {{ total() }} event{{ total() === 1 ? '' : 's' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="card table-card">
        <div class="card-body p-0">
          @if (loadError()) {
            <div class="error-state">
              <p class="mb-2">Failed to load events.</p>
              <button type="button" class="btn btn-sm btn-primary" (click)="loadEvents()">Retry</button>
            </div>
          } @else {
            <ngx-datatable
              class="bootstrap events-table"
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
              (page)="onPage($event)">
              <ngx-datatable-column name="Cover" [flexGrow]="0.8" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="cover-thumb">
                    @if (row.cover_url) {
                      <img [src]="row.cover_url" [alt]="row.title" />
                    } @else {
                      <ng-icon name="bootstrapImage" size="16" />
                    }
                  </div>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Title" prop="title" [flexGrow]="2" [sortable]="true">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="fw-medium text-dark">{{ row.title }}</span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Parlor" [flexGrow]="1.5" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.parlor?.name || '—' }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Type" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="type-badge">{{ row.event_type }}</span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Date" prop="start_time" [flexGrow]="1.3" [sortable]="true">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ formatDateTime(row.start_time) }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Participants" [flexGrow]="1.2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span
                    class="participants-count"
                    [class.participants-count--full]="row.participant_count >= row.max_participants">
                    {{ row.participant_count }}/{{ row.max_participants }}
                  </span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Entry Fee" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  @if (row.entry_fee > 0) {
                    {{ row.entry_fee | currencyIn }}
                  } @else {
                    <span class="text-muted">Free</span>
                  }
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Status" prop="status" [flexGrow]="1" [sortable]="true">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <app-status-badge [status]="row.status" />
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Actions" [flexGrow]="1.5" [sortable]="false" [resizeable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="d-flex align-items-center gap-2">
                    <select
                      class="form-select form-select-sm status-select"
                      [ngModel]="row.status"
                      [disabled]="actionId() === row.id"
                      (ngModelChange)="changeStatus(row, $event)">
                      @for (s of eventStatuses; track s) {
                        <option [value]="s">{{ s }}</option>
                      }
                    </select>
                    <button
                      type="button"
                      class="btn btn-sm btn-light text-danger"
                      [disabled]="actionId() === row.id"
                      (click)="deleteEvent(row)"
                      aria-label="Delete event">
                      <ng-icon name="bootstrapTrash" size="14" />
                    </button>
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
              <div class="empty-state">No events found</div>
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

    .events-table { box-shadow: none; }

    .cover-thumb {
      width: 40px;
      height: 40px;
      border-radius: 0.5rem;
      background: #f3f2f7;
      color: #7367f0;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }

    .cover-thumb img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .type-badge {
      display: inline-block;
      padding: 0.125rem 0.5rem;
      border-radius: 0.25rem;
      font-size: 0.6875rem;
      font-weight: 600;
      text-transform: capitalize;
      background: rgba(115, 103, 240, 0.1);
      color: #7367f0;
    }

    .participants-count { font-weight: 600; font-variant-numeric: tabular-nums; }
    .participants-count--full { color: #ff9f43; }

    .status-select { min-width: 6.5rem; max-width: 7.5rem; }

    .datatable-footer-inner {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 1rem;
      width: 100%;
      padding: 0.5rem 1rem;
    }

    .page-size-select { display: flex; align-items: center; }
    .page-size-select .form-select { width: auto; min-width: 4.5rem; }

    .empty-state, .error-state {
      padding: 2.5rem 1rem;
      text-align: center;
      color: #b9b9c3;
      font-size: 0.875rem;
    }
  `,
})
export class EventsListComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly searchSubject = new Subject<string>();

  readonly rows = signal<ParlourEvent[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly pageSize = signal(20);
  readonly loading = signal(false);
  readonly loadError = signal(false);
  readonly searchInput = signal('');
  readonly statusFilter = signal('');
  readonly actionId = signal<string | null>(null);

  readonly eventStatuses = EVENT_STATUSES;
  readonly pageSizes = [10, 20, 50];
  protected readonly ColumnMode = ColumnMode;

  readonly totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize())));

  ngOnInit(): void {
    this.searchSubject
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe(term => {
        this.searchInput.set(term);
        this.page.set(1);
        this.loadEvents();
      });

    this.loadEvents();
  }

  onSearchChange(value: string): void {
    this.searchSubject.next(value);
  }

  onStatusChange(value: string): void {
    this.statusFilter.set(value);
    this.page.set(1);
    this.loadEvents();
  }

  onPageSizeChange(size: number | string): void {
    this.pageSize.set(Number(size));
    this.page.set(1);
    this.loadEvents();
  }

  onPage(event: { offset: number }): void {
    this.page.set(event.offset + 1);
    this.loadEvents();
  }

  setPage(nextPage: number): void {
    if (nextPage < 1 || nextPage > this.totalPages()) return;
    this.page.set(nextPage);
    this.loadEvents();
  }

  endRow(offset: number, pageSize: number, rowCount: number): number {
    return Math.min(offset * pageSize + rowCount, this.total());
  }

  formatDateTime(value: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '—';
    return date.toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  changeStatus(event: ParlourEvent, status: string): void {
    if (event.status === status) return;
    this.actionId.set(event.id);
    this.api
      .updateEventStatus(event.id, status)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionId.set(null);
          this.toast.success('Event status updated');
          this.loadEvents();
        },
        error: () => {
          this.actionId.set(null);
          this.toast.error('Failed to update status');
        },
      });
  }

  async deleteEvent(event: ParlourEvent): Promise<void> {
    const confirmed = await this.confirm.confirmDanger(
      'Delete Event',
      `Permanently delete "${event.title}"?`,
    );
    if (!confirmed) return;

    this.actionId.set(event.id);
    this.api
      .deleteEvent(event.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionId.set(null);
          this.toast.success('Event deleted');
          this.loadEvents();
        },
        error: () => {
          this.actionId.set(null);
          this.toast.error('Failed to delete event');
        },
      });
  }

  loadEvents(): void {
    this.loading.set(true);
    this.loadError.set(false);

    const params: Record<string, string | number> = {
      page: this.page(),
      limit: this.pageSize(),
    };

    const search = this.searchInput().trim();
    if (search) params['search'] = search;

    const status = this.statusFilter();
    if (status) params['status'] = status;

    this.api
      .getEvents(params)
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
          this.toast.error('Failed to load events');
        },
      });
  }
}