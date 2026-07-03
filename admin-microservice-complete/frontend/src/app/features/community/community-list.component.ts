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
  bootstrapPinAngleFill,
  bootstrapSearch,
  bootstrapTrash,
} from '@ng-icons/bootstrap-icons';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

import { CommunityPost } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';
import { ConfirmService } from '../../shared/services/confirm.service';

@Component({
  selector: 'app-community-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    NgxDatatableModule,
    NgIcon,
    PageHeaderComponent,
    DateFormatPipe,
  ],
  providers: [
    provideIcons({
      bootstrapSearch,
      bootstrapPinAngleFill,
      bootstrapTrash,
    }),
  ],
  template: `
    <div class="community-page">
      <app-page-header
        title="Community"
        subtitle="Forum discussions and guides"
        [breadcrumbs]="[{ label: 'Home', route: '/dashboard' }, { label: 'Community' }]" />

      <div class="card filters-card mb-4">
        <div class="card-body">
          <div class="row g-3 align-items-end">
            <div class="col-md-8">
              <label class="form-label small text-muted mb-1">Search</label>
              <div class="input-group">
                <span class="input-group-text bg-white border-end-0">
                  <ng-icon name="bootstrapSearch" size="16" class="text-muted" />
                </span>
                <input
                  type="search"
                  class="form-control border-start-0 ps-0"
                  placeholder="Search author or title..."
                  [ngModel]="searchInput()"
                  (ngModelChange)="onSearchChange($event)" />
              </div>
            </div>
            <div class="col-md-4 text-md-end">
              <span class="badge bg-light text-dark results-badge">
                {{ total() }} post{{ total() === 1 ? '' : 's' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="card table-card">
        <div class="card-body p-0">
          @if (loadError()) {
            <div class="error-state">
              <p class="mb-2">Failed to load community posts.</p>
              <button type="button" class="btn btn-sm btn-primary" (click)="loadPosts()">Retry</button>
            </div>
          } @else {
            <ngx-datatable
              class="bootstrap community-table"
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
              [rowClass]="getRowClass"
              (page)="onPage($event)">
              <ngx-datatable-column name="Pin" [flexGrow]="0.7" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="form-check form-switch pin-switch">
                    <input
                      class="form-check-input"
                      type="checkbox"
                      role="switch"
                      [id]="'pin-' + row.id"
                      [checked]="row.is_pinned"
                      [disabled]="actionId() === row.id"
                      (change)="togglePin(row, $any($event.target).checked)" />
                  </div>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Author" [flexGrow]="1.5" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="d-flex align-items-center gap-2">
                    @if (row.is_pinned) {
                      <ng-icon name="bootstrapPinAngleFill" size="14" class="pin-icon" />
                    }
                    <span class="fw-medium">{{ row.author?.name || '—' }}</span>
                  </div>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Title" prop="title" [flexGrow]="2.5" [sortable]="true">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="text-dark">{{ row.title }}</span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Tag" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  @if (row.tag) {
                    <span class="tag-chip">{{ row.tag }}</span>
                  } @else {
                    <span class="text-muted">—</span>
                  }
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Views" prop="views_count" [flexGrow]="0.8" [sortable]="true">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ formatCount(row.views_count) }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Likes" prop="likes_count" [flexGrow]="0.8" [sortable]="true">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ formatCount(row.likes_count) }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Comments" prop="comments_count" [flexGrow]="0.9" [sortable]="true">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ formatCount(row.comments_count) }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Date" prop="created_at" [flexGrow]="1.1" [sortable]="true">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.created_at | dateFormat }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Actions" [flexGrow]="0.7" [sortable]="false" [resizeable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <button
                    type="button"
                    class="btn btn-sm btn-light text-danger"
                    [disabled]="actionId() === row.id"
                    (click)="deletePost(row)"
                    aria-label="Delete post">
                    <ng-icon name="bootstrapTrash" size="14" />
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
              <div class="empty-state">No community posts found</div>
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

    .community-table { box-shadow: none; }

    :host ::ng-deep .community-table .datatable-body-row.row-pinned .datatable-body-cell:first-child {
      box-shadow: inset 3px 0 0 #ff9f43;
    }

    .pin-switch { margin: 0; padding-left: 2.5rem; }
    .pin-switch .form-check-input { cursor: pointer; }

    .pin-icon { color: #ff9f43; flex-shrink: 0; }

    .tag-chip {
      display: inline-block;
      padding: 0.125rem 0.5rem;
      border-radius: 0.25rem;
      font-size: 0.6875rem;
      font-weight: 600;
      background: rgba(115, 103, 240, 0.1);
      color: #7367f0;
    }

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
export class CommunityListComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly searchSubject = new Subject<string>();

  readonly rows = signal<CommunityPost[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly pageSize = signal(20);
  readonly loading = signal(false);
  readonly loadError = signal(false);
  readonly searchInput = signal('');
  readonly actionId = signal<string | null>(null);

  readonly pageSizes = [10, 20, 50];
  protected readonly ColumnMode = ColumnMode;

  readonly totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize())));

  readonly getRowClass = (row: CommunityPost): Record<string, boolean> => ({
    'row-pinned': row.is_pinned,
  });

  ngOnInit(): void {
    this.searchSubject
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe(term => {
        this.searchInput.set(term);
        this.page.set(1);
        this.loadPosts();
      });

    this.loadPosts();
  }

  onSearchChange(value: string): void {
    this.searchSubject.next(value);
  }

  onPageSizeChange(size: number | string): void {
    this.pageSize.set(Number(size));
    this.page.set(1);
    this.loadPosts();
  }

  onPage(event: { offset: number }): void {
    this.page.set(event.offset + 1);
    this.loadPosts();
  }

  setPage(nextPage: number): void {
    if (nextPage < 1 || nextPage > this.totalPages()) return;
    this.page.set(nextPage);
    this.loadPosts();
  }

  endRow(offset: number, pageSize: number, rowCount: number): number {
    return Math.min(offset * pageSize + rowCount, this.total());
  }

  formatCount(value: number): string {
    if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
    return String(value);
  }

  togglePin(post: CommunityPost, isPinned: boolean): void {
    this.actionId.set(post.id);
    this.api
      .pinCommunityPost(post.id, isPinned)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionId.set(null);
          this.toast.success(isPinned ? 'Post pinned' : 'Post unpinned');
          this.loadPosts();
        },
        error: () => {
          this.actionId.set(null);
          this.toast.error('Failed to update pin status');
        },
      });
  }

  async deletePost(post: CommunityPost): Promise<void> {
    const confirmed = await this.confirm.confirmDanger(
      'Delete Community Post',
      `Permanently delete "${post.title}"?`,
    );
    if (!confirmed) return;

    this.actionId.set(post.id);
    this.api
      .deleteCommunityPost(post.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionId.set(null);
          this.toast.success('Post deleted');
          this.loadPosts();
        },
        error: () => {
          this.actionId.set(null);
          this.toast.error('Failed to delete post');
        },
      });
  }

  loadPosts(): void {
    this.loading.set(true);
    this.loadError.set(false);

    const params: Record<string, string | number> = {
      page: this.page(),
      limit: this.pageSize(),
    };

    const search = this.searchInput().trim();
    if (search) params['search'] = search;

    this.api
      .getCommunity(params)
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
          this.toast.error('Failed to load community posts');
        },
      });
  }
}