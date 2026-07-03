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
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { bootstrapPlus, bootstrapTag } from '@ng-icons/bootstrap-icons';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';

import { Offer, Parlor } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { StatusBadgeComponent } from '../../shared/components/status-badge/status-badge.component';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';

@Component({
  selector: 'app-offers-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    ReactiveFormsModule,
    NgxDatatableModule,
    NgIcon,
    PageHeaderComponent,
    StatusBadgeComponent,
    DateFormatPipe,
  ],
  providers: [provideIcons({ bootstrapTag, bootstrapPlus })],
  template: `
    <div class="offers-page">
      <app-page-header
        title="Offers"
        subtitle="Manage parlor discounts and promotions"
        [breadcrumbs]="[{ label: 'Home', route: '/dashboard' }, { label: 'Offers' }]">
        <button type="button" class="btn btn-sm btn-primary d-inline-flex align-items-center gap-1" (click)="toggleForm()">
          <ng-icon name="bootstrapPlus" size="14" />
          {{ showForm() ? 'Hide Form' : 'Create Offer' }}
        </button>
      </app-page-header>

      @if (showForm()) {
        <div class="card form-card mb-4">
          <div class="card-header border-0 bg-white">
            <h6 class="mb-0 fw-bold">Create New Offer</h6>
          </div>
          <div class="card-body">
            <form [formGroup]="offerForm" (ngSubmit)="submitOffer()">
              <div class="row g-3">
                <div class="col-md-6">
                  <label class="form-label small text-muted">Parlor</label>
                  <select class="form-select" formControlName="parlour_id">
                    <option value="">Select parlor</option>
                    @for (p of parlors(); track p.id) {
                      <option [value]="p.id">{{ p.name }}</option>
                    }
                  </select>
                </div>
                <div class="col-md-6">
                  <label class="form-label small text-muted">Title</label>
                  <input type="text" class="form-control" formControlName="title" placeholder="Offer title" />
                </div>
                <div class="col-12">
                  <label class="form-label small text-muted">Description</label>
                  <textarea
                    class="form-control"
                    rows="2"
                    formControlName="description"
                    placeholder="Optional description"></textarea>
                </div>
                <div class="col-md-4">
                  <label class="form-label small text-muted">Discount Type</label>
                  <select class="form-select" formControlName="discount_type">
                    <option value="percentage">Percentage</option>
                    <option value="flat">Flat Amount</option>
                  </select>
                </div>
                <div class="col-md-4">
                  <label class="form-label small text-muted">Discount Value</label>
                  <input type="number" class="form-control" formControlName="discount_value" min="1" />
                </div>
                <div class="col-md-4 d-flex align-items-end">
                  <div class="form-check">
                    <input class="form-check-input" type="checkbox" formControlName="is_active" id="offerActive" />
                    <label class="form-check-label" for="offerActive">Active</label>
                  </div>
                </div>
                <div class="col-md-6">
                  <label class="form-label small text-muted">Valid From</label>
                  <input type="date" class="form-control" formControlName="valid_from" />
                </div>
                <div class="col-md-6">
                  <label class="form-label small text-muted">Valid Until</label>
                  <input type="date" class="form-control" formControlName="valid_until" />
                </div>
                <div class="col-12">
                  <button
                    type="submit"
                    class="btn btn-primary"
                    [disabled]="offerForm.invalid || submitting()">
                    {{ submitting() ? 'Creating...' : 'Create Offer' }}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      }

      <div class="card table-card">
        <div class="card-body p-0">
          @if (loadError()) {
            <div class="error-state">
              <p class="mb-2">Failed to load offers.</p>
              <button type="button" class="btn btn-sm btn-primary" (click)="loadOffers()">Retry</button>
            </div>
          } @else {
            <ngx-datatable
              class="bootstrap offers-table"
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
              <ngx-datatable-column name="Title" [flexGrow]="2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="d-flex align-items-center gap-2">
                    <ng-icon name="bootstrapTag" size="16" class="text-warning" />
                    <div>
                      <span class="fw-medium d-block">{{ row.title }}</span>
                      @if (row.description) {
                        <small class="text-muted">{{ row.description }}</small>
                      }
                    </div>
                  </div>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Parlor" [flexGrow]="1.5" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.parlor?.name || '—' }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Discount" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  @if (row.discount_type === 'percentage') {
                    {{ row.discount_value }}%
                  } @else {
                    ₹{{ row.discount_value }}
                  }
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Valid Period" [flexGrow]="1.5" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <small>{{ row.valid_from }} – {{ row.valid_until }}</small>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Usage" prop="usage_count" [flexGrow]="0.8" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.usage_count }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Status" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <app-status-badge [status]="row.is_active ? 'active' : 'cancelled'" />
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Created" prop="created_at" [flexGrow]="1.2" [sortable]="false">
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
              <div class="empty-state">No offers found</div>
            }
          }
        </div>
      </div>
    </div>
  `,
  styles: `
    .form-card .card-header,
    .form-card .card-body { padding: 1.25rem 1.5rem; }

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
export class OffersListComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly fb = inject(FormBuilder);
  private readonly destroyRef = inject(DestroyRef);

  readonly rows = signal<Offer[]>([]);
  readonly parlors = signal<Parlor[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly pageSize = signal(20);
  readonly loading = signal(false);
  readonly loadError = signal(false);
  readonly showForm = signal(false);
  readonly submitting = signal(false);

  readonly totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize())));

  readonly offerForm = this.fb.nonNullable.group({
    parlour_id: ['', Validators.required],
    title: ['', [Validators.required, Validators.minLength(3)]],
    description: [''],
    discount_type: ['percentage' as 'percentage' | 'flat', Validators.required],
    discount_value: [10, [Validators.required, Validators.min(1)]],
    valid_from: ['', Validators.required],
    valid_until: ['', Validators.required],
    is_active: [true],
  });

  protected readonly ColumnMode = ColumnMode;

  ngOnInit(): void {
    this.loadParlors();
    this.loadOffers();
  }

  toggleForm(): void {
    this.showForm.update(v => !v);
  }

  onPage(event: { offset: number }): void {
    this.page.set(event.offset + 1);
    this.loadOffers();
  }

  setPage(nextPage: number): void {
    if (nextPage < 1 || nextPage > this.totalPages()) return;
    this.page.set(nextPage);
    this.loadOffers();
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

  submitOffer(): void {
    if (this.offerForm.invalid) return;

    this.submitting.set(true);
    const value = this.offerForm.getRawValue();

    this.api
      .createOffer({
        parlour_id: value.parlour_id,
        title: value.title,
        description: value.description || undefined,
        discount_type: value.discount_type,
        discount_value: value.discount_value,
        valid_from: value.valid_from,
        valid_until: value.valid_until,
        is_active: value.is_active,
      })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.submitting.set(false);
          this.toast.success('Offer created');
          this.offerForm.reset({
            parlour_id: '',
            title: '',
            description: '',
            discount_type: 'percentage',
            discount_value: 10,
            valid_from: '',
            valid_until: '',
            is_active: true,
          });
          this.showForm.set(false);
          this.page.set(1);
          this.loadOffers();
        },
        error: () => {
          this.submitting.set(false);
          this.toast.error('Failed to create offer');
        },
      });
  }

  loadOffers(): void {
    this.loading.set(true);
    this.loadError.set(false);

    this.api
      .getOffers({ page: this.page(), limit: this.pageSize() })
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
          this.toast.error('Failed to load offers');
        },
      });
  }
}