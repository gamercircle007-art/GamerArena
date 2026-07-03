import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { bootstrapStarFill, bootstrapTrash } from '@ng-icons/bootstrap-icons';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';

import { Rating } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { ToastService } from '../../core/services/toast.service';
import { EmptyStateComponent } from '../../shared/components/empty-state/empty-state.component';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';
import { TruncatePipe } from '../../shared/pipes/truncate.pipe';
import { ConfirmService } from '../../shared/services/confirm.service';

@Component({
  selector: 'app-ratings-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    NgxDatatableModule,
    NgIcon,
    PageHeaderComponent,
    EmptyStateComponent,
    DateFormatPipe,
    TruncatePipe,
  ],
  providers: [provideIcons({ bootstrapStarFill, bootstrapTrash })],
  template: `
    <div class="ratings-page">
      <app-page-header
        title="Ratings"
        subtitle="Parlor reviews and star ratings"
        [breadcrumbs]="[{ label: 'Home', route: '/dashboard' }, { label: 'Ratings' }]" />

      <div class="card table-card">
        <div class="card-body p-0">
          @if (loadError()) {
            <div class="error-state">
              <p class="mb-2">Failed to load ratings.</p>
              <button type="button" class="btn btn-sm btn-primary" (click)="load()">Retry</button>
            </div>
          } @else {
            <ngx-datatable
              class="bootstrap"
              [rows]="rows()"
              [columnMode]="ColumnMode.force"
              [headerHeight]="48"
              [rowHeight]="56"
              [footerHeight]="0"
              [loadingIndicator]="loading()">
              <ngx-datatable-column name="User" [flexGrow]="1.5">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.user?.name ?? '—' }}
                </ng-template>
              </ngx-datatable-column>
              <ngx-datatable-column name="Parlor" [flexGrow]="1.5">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.parlor?.name ?? '—' }}
                </ng-template>
              </ngx-datatable-column>
              <ngx-datatable-column name="Rating" prop="rating" [flexGrow]="1">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="rating-stars">
                    @for (s of stars(row.rating); track $index) {
                      <ng-icon name="bootstrapStarFill" size="12" [class.filled]="s" />
                    }
                    {{ row.rating }}
                  </span>
                </ng-template>
              </ngx-datatable-column>
              <ngx-datatable-column name="Review" [flexGrow]="2.5">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.review | truncate: 80 }}
                </ng-template>
              </ngx-datatable-column>
              <ngx-datatable-column name="Date" [flexGrow]="1">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.created_at | dateFormat }}
                </ng-template>
              </ngx-datatable-column>
              <ngx-datatable-column name="Actions" [flexGrow]="0.8">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <button
                    type="button"
                    class="btn btn-sm btn-outline-danger"
                    (click)="deleteRating(row)">
                    <ng-icon name="bootstrapTrash" size="14" />
                  </button>
                </ng-template>
              </ngx-datatable-column>
            </ngx-datatable>
            @if (!loading() && !rows().length) {
              <app-empty-state title="No ratings yet" message="User reviews will appear here." />
            }
          }
        </div>
      </div>
    </div>
  `,
  styles: `
    .rating-stars { display: inline-flex; align-items: center; gap: 2px; color: #d8d6de; }
    .rating-stars .filled { color: #ff9f43; }
    .error-state { padding: 2rem; text-align: center; }
  `,
})
export class RatingsListComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly destroyRef = inject(DestroyRef);

  readonly rows = signal<Rating[]>([]);
  readonly loading = signal(false);
  readonly loadError = signal(false);
  protected readonly ColumnMode = ColumnMode;

  ngOnInit(): void {
    this.load();
  }

  stars(rating: number): boolean[] {
    return Array.from({ length: 5 }, (_, i) => i < Math.round(rating));
  }

  load(): void {
    this.loading.set(true);
    this.loadError.set(false);
    this.api
      .getRatings({ page: 1, limit: 50 })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.rows.set(res.items);
          this.loading.set(false);
        },
        error: () => {
          this.loading.set(false);
          this.loadError.set(true);
        },
      });
  }

  async deleteRating(row: Rating): Promise<void> {
    const ok = await this.confirm.confirmDanger('Delete Rating', 'Remove this review permanently?');
    if (!ok) return;
    this.api
      .deleteRating(row.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.toast.success('Rating deleted');
          this.load();
        },
        error: () => this.toast.error('Failed to delete rating'),
      });
  }
}