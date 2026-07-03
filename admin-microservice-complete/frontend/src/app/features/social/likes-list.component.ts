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
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  bootstrapHeart,
  bootstrapHeartFill,
  bootstrapPerson,
  bootstrapTrash,
} from '@ng-icons/bootstrap-icons';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';

import { Like } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { MockDataService } from '../../core/services/mock-data.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';
import { TruncatePipe } from '../../shared/pipes/truncate.pipe';
import { ConfirmService } from '../../shared/services/confirm.service';

@Component({
  selector: 'app-likes-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    NgxDatatableModule,
    NgIcon,
    PageHeaderComponent,
    DateFormatPipe,
    TruncatePipe,
  ],
  providers: [
    provideIcons({
      bootstrapPerson,
      bootstrapHeart,
      bootstrapHeartFill,
      bootstrapTrash,
    }),
  ],
  template: `
    <div class="likes-page">
      <app-page-header
        title="Likes"
        subtitle="Monitor user engagement across posts and comments"
        [breadcrumbs]="[
          { label: 'Home', route: '/dashboard' },
          { label: 'Social', route: '/social/likes' },
          { label: 'Likes' },
        ]" />

      <div class="row g-3 mb-4">
        <div class="col-md-4">
          <div class="card stat-card h-100">
            <div class="card-body d-flex align-items-center gap-3">
              <div class="stat-icon stat-icon--primary">
                <ng-icon name="bootstrapHeartFill" size="20" />
              </div>
              <div>
                <div class="stat-value">{{ likeStats().today }}</div>
                <div class="stat-label">Likes Today</div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card stat-card h-100">
            <div class="card-body d-flex align-items-center gap-3">
              <div class="stat-icon stat-icon--info">
                <ng-icon name="bootstrapHeart" size="20" />
              </div>
              <div>
                <div class="stat-value">{{ likeStats().thisWeek }}</div>
                <div class="stat-label">Likes This Week</div>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card stat-card h-100">
            <div class="card-body">
              <div class="stat-label mb-1">Most Liked Post</div>
              @if (likeStats().mostLikedPost; as top) {
                <div class="stat-preview">{{ top.preview | truncate: 60 }}</div>
                <small class="text-muted">{{ top.count }} like{{ top.count === 1 ? '' : 's' }}</small>
              } @else {
                <span class="text-muted small">No data</span>
              }
            </div>
          </div>
        </div>
      </div>

      <div class="card table-card">
        <div class="card-body p-0">
          @if (loadError()) {
            <div class="error-state">
              <p class="mb-2">Failed to load likes.</p>
              <button type="button" class="btn btn-sm btn-primary" (click)="loadLikes()">
                Retry
              </button>
            </div>
          } @else {
            <ngx-datatable
              class="bootstrap likes-table"
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
                    <div class="user-avatar">
                      @if (row.user?.avatar_url) {
                        <img [src]="row.user!.avatar_url!" [alt]="userName(row)" />
                      } @else {
                        <ng-icon name="bootstrapPerson" size="18" />
                      }
                    </div>
                    <span class="fw-medium">{{ userName(row) }}</span>
                  </div>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Target Type" [flexGrow]="1.2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="target-badge" [class]="'target-' + row.target_type">
                    {{ row.target_type }}
                  </span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Target Preview" [flexGrow]="2.5" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="preview-text">{{ row.target_preview || '—' | truncate: 70 }}</span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Parlor" prop="parlor_name" [flexGrow]="1.5" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.parlor_name || '—' }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Date" prop="created_at" [flexGrow]="1.3" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.created_at | dateFormat }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Actions" [flexGrow]="0.8" [sortable]="false" [resizeable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <button
                    type="button"
                    class="btn btn-sm btn-outline-danger"
                    [disabled]="actionId() === row.id"
                    (click)="removeLike(row)">
                    <ng-icon name="bootstrapTrash" size="14" />
                    Remove
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

            @if (!loading() && !rows().length) {
              <div class="empty-state">No likes found</div>
            }
          }
        </div>
      </div>
    </div>
  `,
  styles: `
    .stat-card .card-body { padding: 1.25rem 1.5rem; }

    .stat-icon {
      width: 44px;
      height: 44px;
      border-radius: 0.5rem;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .stat-icon--primary { background: rgba(234, 84, 85, 0.12); color: #ea5455; }
    .stat-icon--info { background: rgba(115, 103, 240, 0.12); color: #7367f0; }

    .stat-value { font-size: 1.5rem; font-weight: 700; line-height: 1.2; }
    .stat-label { font-size: 0.8125rem; color: #6e6b7b; }
    .stat-preview { font-size: 0.875rem; font-weight: 500; line-height: 1.35; }

    .user-avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: #f3f2f7;
      color: #7367f0;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      overflow: hidden;
    }

    .user-avatar img { width: 100%; height: 100%; object-fit: cover; }

    .target-badge {
      display: inline-block;
      padding: 0.25rem 0.625rem;
      border-radius: 0.375rem;
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: capitalize;
    }

    .target-post { background: rgba(115, 103, 240, 0.12); color: #7367f0; }
    .target-comment { background: rgba(0, 207, 232, 0.12); color: #00cfe8; }
    .target-reel { background: rgba(255, 159, 67, 0.12); color: #ff9f43; }

    .preview-text { font-size: 0.875rem; color: #5e5873; }

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
export class LikesListComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly mock = inject(MockDataService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly destroyRef = inject(DestroyRef);

  readonly rows = signal<Like[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly pageSize = signal(20);
  readonly loading = signal(false);
  readonly loadError = signal(false);
  readonly actionId = signal<string | null>(null);

  readonly likeStats = computed(() => this.mock.computeLikeStats());
  readonly totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize())));

  protected readonly ColumnMode = ColumnMode;

  ngOnInit(): void {
    this.loadLikes();
  }

  userName(row: Like): string {
    return row.user?.name ?? 'Unknown User';
  }

  onPage(event: { offset: number }): void {
    this.page.set(event.offset + 1);
    this.loadLikes();
  }

  setPage(nextPage: number): void {
    if (nextPage < 1 || nextPage > this.totalPages()) return;
    this.page.set(nextPage);
    this.loadLikes();
  }

  endRow(offset: number, pageSize: number, rowCount: number): number {
    return Math.min(offset * pageSize + rowCount, this.total());
  }

  loadLikes(): void {
    this.loading.set(true);
    this.loadError.set(false);

    this.api
      .getLikes({ page: this.page(), limit: this.pageSize() })
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
          this.toast.error('Failed to load likes');
        },
      });
  }

  async removeLike(like: Like): Promise<void> {
    const confirmed = await this.confirm.confirmDanger(
      'Remove Like',
      `Remove this like by "${this.userName(like)}"?`,
    );
    if (!confirmed) return;

    this.actionId.set(like.id);
    this.api
      .deleteLike(like.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionId.set(null);
          this.toast.success('Like removed');
          this.loadLikes();
        },
        error: () => {
          this.actionId.set(null);
          this.toast.error('Failed to remove like');
        },
      });
  }
}