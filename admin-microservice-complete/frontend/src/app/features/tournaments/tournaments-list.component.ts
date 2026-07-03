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
  bootstrapChevronDown,
  bootstrapSearch,
  bootstrapThreeDotsVertical,
  bootstrapTrash,
} from '@ng-icons/bootstrap-icons';
import { BsDropdownModule } from 'ngx-bootstrap/dropdown';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

import { Tournament, TournamentStatus } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { StatusBadgeComponent } from '../../shared/components/status-badge/status-badge.component';
import { CurrencyInPipe } from '../../shared/pipes/currency-in.pipe';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';
import { ConfirmService } from '../../shared/services/confirm.service';

const STATUS_OPTIONS: { value: TournamentStatus | ''; label: string }[] = [
  { value: '', label: 'All Status' },
  { value: 'draft', label: 'Draft' },
  { value: 'open', label: 'Open' },
  { value: 'full', label: 'Full' },
  { value: 'live', label: 'Live' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
];

const CHANGEABLE_STATUSES: TournamentStatus[] = [
  'draft',
  'open',
  'full',
  'live',
  'completed',
  'cancelled',
];

@Component({
  selector: 'app-tournaments-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    NgxDatatableModule,
    BsDropdownModule,
    NgIcon,
    PageHeaderComponent,
    StatusBadgeComponent,
    DateFormatPipe,
    CurrencyInPipe,
  ],
  providers: [
    provideIcons({
      bootstrapSearch,
      bootstrapThreeDotsVertical,
      bootstrapChevronDown,
      bootstrapTrash,
    }),
  ],
  template: `
    <div class="tournaments-page">
      <app-page-header
        title="Tournaments"
        subtitle="Manage tournament listings and status"
        [breadcrumbs]="[
          { label: 'Home', route: '/dashboard' },
          { label: 'Tournaments' },
        ]" />

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
                  placeholder="Search title, game, parlor..."
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
                @for (opt of statusOptions; track opt.value) {
                  <option [value]="opt.value">{{ opt.label }}</option>
                }
              </select>
            </div>
            <div class="col-md-3 text-md-end">
              <span class="badge bg-light text-dark results-badge">
                {{ total() }} tournament{{ total() === 1 ? '' : 's' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="card table-card">
        <div class="card-body p-0">
          @if (loadError()) {
            <div class="error-state">
              <p class="mb-2">Failed to load tournaments.</p>
              <button type="button" class="btn btn-sm btn-primary" (click)="loadTournaments()">
                Retry
              </button>
            </div>
          } @else {
            <ngx-datatable
              class="bootstrap tournaments-table"
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
              <ngx-datatable-column name="Title" prop="title" [flexGrow]="2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="fw-medium">{{ row.title }}</span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Parlor" [flexGrow]="1.5" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.parlor?.name || '—' }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Game" prop="game_type" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="game-chip">{{ row.game_type }}</span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Slots" [flexGrow]="1.8" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="slots-cell">
                    <div class="progress slots-progress">
                      <div
                        class="progress-bar"
                        [style.width.%]="slotPercent(row)"
                        [class.bg-success]="slotPercent(row) < 80"
                        [class.bg-warning]="slotPercent(row) >= 80 && slotPercent(row) < 100"
                        [class.bg-danger]="slotPercent(row) >= 100"></div>
                    </div>
                    <small class="text-muted">
                      {{ row.booked_slots }}/{{ row.total_slots }}
                    </small>
                  </div>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Entry Fee" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.entry_fee | currencyIn }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Date" prop="start_time" [flexGrow]="1.3" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.start_time | dateFormat }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Status" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <app-status-badge [status]="row.status" />
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Actions" [flexGrow]="1" [sortable]="false" [resizeable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="dropdown" dropdown container="body" [dropup]="true">
                    <button
                      type="button"
                      class="btn btn-sm btn-light actions-btn"
                      dropdownToggle
                      aria-label="Tournament actions">
                      <ng-icon name="bootstrapThreeDotsVertical" size="16" />
                    </button>
                    <ul *dropdownMenu class="dropdown-menu dropdown-menu-end shadow-sm">
                      <li class="dropdown-header small text-muted">Change Status</li>
                      @for (status of changeableStatuses; track status) {
                        <li>
                          <button
                            type="button"
                            class="dropdown-item"
                            [class.active]="row.status === status"
                            [disabled]="actionId() === row.id"
                            (click)="changeStatus(row, status)">
                            {{ formatStatus(status) }}
                          </button>
                        </li>
                      }
                      <li><hr class="dropdown-divider" /></li>
                      <li>
                        <button
                          type="button"
                          class="dropdown-item text-danger"
                          [disabled]="actionId() === row.id"
                          (click)="deleteTournament(row)">
                          <ng-icon name="bootstrapTrash" size="14" class="me-1" />
                          Delete
                        </button>
                      </li>
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
              <div class="empty-state">No tournaments found</div>
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

    .game-chip {
      display: inline-block;
      padding: 0.2rem 0.5rem;
      border-radius: 0.375rem;
      font-size: 0.75rem;
      font-weight: 600;
      background: #f3f2f7;
      color: #6e6b7b;
    }

    .slots-cell { min-width: 100px; }

    .slots-progress {
      height: 6px;
      margin-bottom: 0.25rem;
      background: #ebe9f1;
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

    .empty-state,
    .error-state {
      padding: 2.5rem 1rem;
      text-align: center;
      color: #b9b9c3;
      font-size: 0.875rem;
    }
  `,
})
export class TournamentsListComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly searchSubject = new Subject<string>();

  readonly rows = signal<Tournament[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly pageSize = signal(20);
  readonly loading = signal(false);
  readonly loadError = signal(false);
  readonly searchInput = signal('');
  readonly statusFilter = signal<TournamentStatus | ''>('');
  readonly actionId = signal<string | null>(null);

  readonly statusOptions = STATUS_OPTIONS;
  readonly changeableStatuses = CHANGEABLE_STATUSES;
  readonly totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize())));

  protected readonly ColumnMode = ColumnMode;

  ngOnInit(): void {
    this.searchSubject
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe(term => {
        this.searchInput.set(term);
        this.page.set(1);
        this.loadTournaments();
      });

    this.loadTournaments();
  }

  formatStatus(status: TournamentStatus): string {
    return status.replace(/_/g, ' ');
  }

  slotPercent(row: Tournament): number {
    if (!row.total_slots) return 0;
    return Math.min(100, Math.round((row.booked_slots / row.total_slots) * 100));
  }

  onSearchChange(value: string): void {
    this.searchSubject.next(value);
  }

  onStatusChange(value: TournamentStatus | ''): void {
    this.statusFilter.set(value);
    this.page.set(1);
    this.loadTournaments();
  }

  onPage(event: { offset: number }): void {
    this.page.set(event.offset + 1);
    this.loadTournaments();
  }

  setPage(nextPage: number): void {
    if (nextPage < 1 || nextPage > this.totalPages()) return;
    this.page.set(nextPage);
    this.loadTournaments();
  }

  endRow(offset: number, pageSize: number, rowCount: number): number {
    return Math.min(offset * pageSize + rowCount, this.total());
  }

  loadTournaments(): void {
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
      .getTournaments(params)
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
          this.toast.error('Failed to load tournaments');
        },
      });
  }

  changeStatus(tournament: Tournament, status: TournamentStatus): void {
    if (tournament.status === status) return;

    this.actionId.set(tournament.id);
    this.api
      .updateTournamentStatus(tournament.id, status)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionId.set(null);
          this.toast.success(`Status changed to ${this.formatStatus(status)}`);
          this.loadTournaments();
        },
        error: () => {
          this.actionId.set(null);
          this.toast.error('Failed to update status');
        },
      });
  }

  async deleteTournament(tournament: Tournament): Promise<void> {
    const confirmed = await this.confirm.confirmDanger(
      'Delete Tournament',
      `Permanently delete "${tournament.title}"? This cannot be undone.`,
    );
    if (!confirmed) return;

    this.actionId.set(tournament.id);
    this.api
      .deleteTournament(tournament.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionId.set(null);
          this.toast.success('Tournament deleted');
          this.loadTournaments();
        },
        error: () => {
          this.actionId.set(null);
          this.toast.error('Failed to delete tournament');
        },
      });
  }
}