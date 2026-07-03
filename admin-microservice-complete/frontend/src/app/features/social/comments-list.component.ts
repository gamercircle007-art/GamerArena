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
  bootstrapArrowCounterclockwise,
  bootstrapPerson,
  bootstrapSearch,
  bootstrapTrash,
} from '@ng-icons/bootstrap-icons';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

import { Comment } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { StatusBadgeComponent } from '../../shared/components/status-badge/status-badge.component';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';
import { TruncatePipe } from '../../shared/pipes/truncate.pipe';
import { ConfirmService } from '../../shared/services/confirm.service';

@Component({
  selector: 'app-comments-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    NgxDatatableModule,
    NgIcon,
    PageHeaderComponent,
    StatusBadgeComponent,
    DateFormatPipe,
    TruncatePipe,
  ],
  providers: [
    provideIcons({
      bootstrapSearch,
      bootstrapPerson,
      bootstrapTrash,
      bootstrapArrowCounterclockwise,
    }),
  ],
  template: `
    <div class="comments-page">
      <app-page-header
        title="Comments"
        subtitle="Moderate user comments across posts"
        [breadcrumbs]="[
          { label: 'Home', route: '/dashboard' },
          { label: 'Social', route: '/social/comments' },
          { label: 'Comments' },
        ]" />

      <div class="card filters-card mb-4">
        <div class="card-body">
          <div class="row g-3 align-items-end">
            <div class="col-md-6">
              <label class="form-label small text-muted mb-1">Search</label>
              <div class="input-group">
                <span class="input-group-text bg-white border-end-0">
                  <ng-icon name="bootstrapSearch" size="16" class="text-muted" />
                </span>
                <input
                  type="search"
                  class="form-control border-start-0 ps-0"
                  placeholder="Search comment, user, post..."
                  [ngModel]="searchInput()"
                  (ngModelChange)="onSearchChange($event)" />
              </div>
            </div>
            <div class="col-md-3">
              <div class="form-check form-switch mt-md-4">
                <input
                  class="form-check-input"
                  type="checkbox"
                  id="showDeleted"
                  [ngModel]="showDeleted()"
                  (ngModelChange)="onShowDeletedChange($event)" />
                <label class="form-check-label small" for="showDeleted">Show deleted</label>
              </div>
            </div>
            <div class="col-md-3 text-md-end">
              <span class="badge bg-light text-dark results-badge">
                {{ total() }} comment{{ total() === 1 ? '' : 's' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div class="card table-card">
        <div class="card-body p-0">
          @if (loadError()) {
            <div class="error-state">
              <p class="mb-2">Failed to load comments.</p>
              <button type="button" class="btn btn-sm btn-primary" (click)="loadComments()">
                Retry
              </button>
            </div>
          } @else {
            <ngx-datatable
              class="bootstrap comments-table"
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
              <ngx-datatable-column name="User" [flexGrow]="1.8" [sortable]="false">
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

              <ngx-datatable-column name="Comment" [flexGrow]="2.5" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span
                    class="comment-text"
                    [class.comment-text--deleted]="row.is_deleted">
                    {{ row.content | truncate: 80 }}
                  </span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Post Preview" [flexGrow]="2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="text-muted small">{{ row.post_preview || '—' | truncate: 60 }}</span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Likes" prop="likes_count" [flexGrow]="0.8" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.likes_count }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Replies" prop="reply_count" [flexGrow]="0.8" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.reply_count }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Status" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <app-status-badge [status]="row.is_deleted ? 'deleted' : 'active'" />
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Date" prop="created_at" [flexGrow]="1.2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.created_at | dateFormat }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Actions" [flexGrow]="1.2" [sortable]="false" [resizeable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  @if (row.is_deleted) {
                    <button
                      type="button"
                      class="btn btn-sm btn-outline-success"
                      [disabled]="actionId() === row.id"
                      (click)="restoreComment(row)">
                      <ng-icon name="bootstrapArrowCounterclockwise" size="14" />
                      Restore
                    </button>
                  } @else {
                    <button
                      type="button"
                      class="btn btn-sm btn-outline-danger"
                      [disabled]="actionId() === row.id"
                      (click)="removeComment(row)">
                      <ng-icon name="bootstrapTrash" size="14" />
                      Remove
                    </button>
                  }
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
              <div class="empty-state">No comments found</div>
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

    .comment-text { font-size: 0.875rem; }
    .comment-text--deleted {
      text-decoration: line-through;
      color: #b9b9c3;
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
export class CommentsListComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly destroyRef = inject(DestroyRef);
  private readonly searchSubject = new Subject<string>();

  readonly rows = signal<Comment[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly pageSize = signal(20);
  readonly loading = signal(false);
  readonly loadError = signal(false);
  readonly searchInput = signal('');
  readonly showDeleted = signal(false);
  readonly actionId = signal<string | null>(null);

  readonly totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize())));

  protected readonly ColumnMode = ColumnMode;

  ngOnInit(): void {
    this.searchSubject
      .pipe(debounceTime(300), distinctUntilChanged(), takeUntilDestroyed(this.destroyRef))
      .subscribe(term => {
        this.searchInput.set(term);
        this.page.set(1);
        this.loadComments();
      });

    this.loadComments();
  }

  userName(row: Comment): string {
    return row.user?.name ?? 'Unknown User';
  }

  onSearchChange(value: string): void {
    this.searchSubject.next(value);
  }

  onShowDeletedChange(value: boolean): void {
    this.showDeleted.set(value);
    this.page.set(1);
    this.loadComments();
  }

  onPage(event: { offset: number }): void {
    this.page.set(event.offset + 1);
    this.loadComments();
  }

  setPage(nextPage: number): void {
    if (nextPage < 1 || nextPage > this.totalPages()) return;
    this.page.set(nextPage);
    this.loadComments();
  }

  endRow(offset: number, pageSize: number, rowCount: number): number {
    return Math.min(offset * pageSize + rowCount, this.total());
  }

  loadComments(): void {
    this.loading.set(true);
    this.loadError.set(false);

    const params: Record<string, string | number | boolean> = {
      page: this.page(),
      limit: this.pageSize(),
    };

    const search = this.searchInput().trim();
    if (search) params['search'] = search;

    if (!this.showDeleted()) {
      params['is_deleted'] = false;
    }

    this.api
      .getComments(params)
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
          this.toast.error('Failed to load comments');
        },
      });
  }

  async removeComment(comment: Comment): Promise<void> {
    const confirmed = await this.confirm.confirmDanger(
      'Remove Comment',
      `Remove this comment by "${this.userName(comment)}"?`,
    );
    if (!confirmed) return;

    this.actionId.set(comment.id);
    this.api
      .deleteComment(comment.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionId.set(null);
          this.toast.success('Comment removed');
          this.loadComments();
        },
        error: () => {
          this.actionId.set(null);
          this.toast.error('Failed to remove comment');
        },
      });
  }

  restoreComment(comment: Comment): void {
    this.actionId.set(comment.id);
    this.api
      .restoreComment(comment.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionId.set(null);
          this.toast.success('Comment restored');
          this.loadComments();
        },
        error: () => {
          this.actionId.set(null);
          this.toast.error('Failed to restore comment');
        },
      });
  }
}