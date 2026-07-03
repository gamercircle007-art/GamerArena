import {
  ChangeDetectionStrategy,
  Component,
  computed,
  DestroyRef,
  inject,
  OnInit,
  signal,
  TemplateRef,
  ViewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  bootstrapChat,
  bootstrapEye,
  bootstrapGeoAlt,
  bootstrapHeart,
  bootstrapPlayFill,
  bootstrapSearch,
  bootstrapShop,
  bootstrapTrash,
} from '@ng-icons/bootstrap-icons';
import { BsDropdownModule } from 'ngx-bootstrap/dropdown';
import { BsModalRef, BsModalService, ModalModule } from 'ngx-bootstrap/modal';
import { TabsModule } from 'ngx-bootstrap/tabs';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

import { hasPermission, PERMISSIONS } from '../../core/constants/permissions';
import { MediaType, Post } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';
import { TruncatePipe } from '../../shared/pipes/truncate.pipe';
import { ConfirmService } from '../../shared/services/confirm.service';
import { MediaViewerComponent } from './media-viewer.component';

type MediaTab = '' | MediaType;

const MEDIA_TABS: { key: MediaTab; label: string }[] = [
  { key: '', label: 'All' },
  { key: 'image', label: 'Images' },
  { key: 'video', label: 'Videos' },
  { key: 'reel', label: 'Reels' },
];

@Component({
  selector: 'app-posts-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    NgxDatatableModule,
    BsDropdownModule,
    ModalModule,
    TabsModule,
    NgIcon,
    PageHeaderComponent,
    DateFormatPipe,
    TruncatePipe,
    MediaViewerComponent,
  ],
  providers: [
    provideIcons({
      bootstrapSearch,
      bootstrapShop,
      bootstrapHeart,
      bootstrapChat,
      bootstrapGeoAlt,
      bootstrapPlayFill,
      bootstrapEye,
      bootstrapTrash,
    }),
  ],
  template: `
    <div class="posts-page">
      <app-page-header
        title="Posts"
        subtitle="Parlor social feed — text, images, videos, and reels"
        [breadcrumbs]="[{ label: 'Home', route: '/dashboard' }, { label: 'Posts' }]" />

      <div class="card filters-card mb-4">
        <div class="card-body">
          <tabset class="media-tabs mb-3">
            @for (tab of mediaTabs; track tab.key) {
              <tab
                [heading]="tab.label"
                [active]="mediaTab() === tab.key"
                (selectTab)="setMediaTab(tab.key)" />
            }
          </tabset>

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
                  placeholder="Search content or parlor..."
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
              <p class="mb-2">Failed to load posts.</p>
              <button type="button" class="btn btn-sm btn-primary" (click)="loadPosts()">
                Retry
              </button>
            </div>
          } @else {
            <ngx-datatable
              class="bootstrap posts-table"
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
              (page)="onPage($event)"
              (activate)="onRowActivate($event)">
              <ngx-datatable-column name="Parlor" [flexGrow]="2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="d-flex align-items-center gap-2">
                    <span class="parlor-avatar">
                      <ng-icon name="bootstrapShop" size="14" />
                    </span>
                    <span class="fw-medium text-dark text-truncate">
                      {{ row.parlor?.name || '—' }}
                    </span>
                  </div>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Content" [flexGrow]="3" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="content-cell">{{ row.content | truncate: 80 }}</span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Media Type" [flexGrow]="1.2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="media-badge" [class]="'media-' + row.media_type">
                    {{ row.media_type }}
                  </span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Media" [flexGrow]="1" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  @if (row.media_urls.length && isVisualMedia(row.media_type)) {
                    <div class="thumb-wrap">
                      @if (row.media_type === 'image') {
                        <img [src]="row.media_urls[0]" alt="" class="media-thumb" />
                      } @else {
                        <span class="video-thumb">
                          <ng-icon name="bootstrapPlayFill" size="14" />
                        </span>
                      }
                    </div>
                  } @else {
                    <span class="text-muted small">—</span>
                  }
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Geo" [flexGrow]="0.8" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  @if (row.geo_lat != null && row.geo_lng != null) {
                    <span class="geo-pin" title="{{ row.geo_lat }}, {{ row.geo_lng }}">
                      <ng-icon name="bootstrapGeoAlt" size="16" class="text-danger" />
                    </span>
                  } @else {
                    <span class="text-muted">—</span>
                  }
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Likes" [flexGrow]="0.9" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="stat-cell">
                    <ng-icon name="bootstrapHeart" size="12" class="text-danger" />
                    {{ row.likes_count }}
                  </span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Comments" [flexGrow]="0.9" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <span class="stat-cell">
                    <ng-icon name="bootstrapChat" size="12" class="text-primary" />
                    {{ row.comments_count }}
                  </span>
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Date" [flexGrow]="1.2" [sortable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  {{ row.created_at | dateFormat }}
                </ng-template>
              </ngx-datatable-column>

              <ngx-datatable-column name="Actions" [flexGrow]="1" [sortable]="false" [resizeable]="false">
                <ng-template let-row="row" ngx-datatable-cell-template>
                  <div class="d-flex gap-1" (click)="$event.stopPropagation()">
                    <button
                      type="button"
                      class="btn btn-sm btn-light actions-btn"
                      title="View"
                      (click)="openPostModal(row)">
                      <ng-icon name="bootstrapEye" size="14" />
                    </button>
                    @if (canDelete()) {
                      <button
                        type="button"
                        class="btn btn-sm btn-light actions-btn text-danger"
                        title="Delete"
                        [disabled]="actionPostId() === row.id"
                        (click)="deletePost(row)">
                        <ng-icon name="bootstrapTrash" size="14" />
                      </button>
                    }
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
              <div class="empty-state">No posts found</div>
            }
          }
        </div>
      </div>
    </div>

    <ng-template #postModalTpl>
      @if (modalPost(); as post) {
        <div class="modal-header border-0 pb-0">
          <h5 class="modal-title fw-bold">Post Details</h5>
          <button type="button" class="btn-close" aria-label="Close" (click)="closePostModal()"></button>
        </div>
        <div class="modal-body pt-2">
          <app-media-viewer [post]="post" />
        </div>
        <div class="modal-footer border-0 pt-0">
          @if (canDelete()) {
            <button
              type="button"
              class="btn btn-outline-danger btn-sm"
              [disabled]="actionPostId() === post.id"
              (click)="deletePost(post, true)">
              Delete
            </button>
          }
          <button type="button" class="btn btn-light btn-sm" (click)="closePostModal()">Close</button>
        </div>
      }
    </ng-template>
  `,
  styles: `
    .filters-card .card-body { padding: 1.25rem 1.5rem; }

    .results-badge {
      font-size: 0.8125rem;
      font-weight: 600;
      padding: 0.5rem 0.75rem;
      border: 1px solid #ebe9f1;
    }

    .posts-table { box-shadow: none; }

    .parlor-avatar {
      width: 28px;
      height: 28px;
      border-radius: 0.375rem;
      background: rgba(115, 103, 240, 0.12);
      color: #7367f0;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .content-cell { font-size: 0.875rem; color: #5e5873; }

    .media-badge {
      display: inline-block;
      padding: 0.2rem 0.5rem;
      border-radius: 0.25rem;
      font-size: 0.6875rem;
      font-weight: 700;
      text-transform: uppercase;
    }

    .media-text { background: #f3f2f7; color: #6e6b7b; }
    .media-image { background: rgba(0, 207, 232, 0.12); color: #00cfe8; }
    .media-video { background: rgba(115, 103, 240, 0.12); color: #7367f0; }
    .media-reel { background: rgba(234, 84, 85, 0.12); color: #ea5455; }

    .thumb-wrap { display: flex; align-items: center; }

    .media-thumb {
      width: 40px;
      height: 40px;
      border-radius: 0.375rem;
      object-fit: cover;
      border: 1px solid #ebe9f1;
    }

    .video-thumb {
      width: 40px;
      height: 40px;
      border-radius: 0.375rem;
      background: #1e1e2d;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .stat-cell {
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      font-size: 0.875rem;
    }

    .geo-pin { cursor: help; }

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

    :host ::ng-deep .media-tabs .nav-link.active {
      color: #7367f0;
      border-bottom-color: #7367f0;
    }
  `,
})
export class PostsListComponent implements OnInit {
  @ViewChild('postModalTpl') postModalTpl!: TemplateRef<void>;

  private readonly api = inject(AdminApiService);
  private readonly auth = inject(AuthService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly modalService = inject(BsModalService);
  private readonly destroyRef = inject(DestroyRef);

  private readonly searchSubject = new Subject<string>();
  private postModalRef?: BsModalRef;

  readonly rows = signal<Post[]>([]);
  readonly total = signal(0);
  readonly page = signal(1);
  readonly pageSize = signal(20);
  readonly loading = signal(false);
  readonly loadError = signal(false);
  readonly searchInput = signal('');
  readonly mediaTab = signal<MediaTab>('');
  readonly actionPostId = signal<string | null>(null);
  readonly modalPost = signal<Post | null>(null);

  readonly pageSizes = [10, 20, 50];
  readonly mediaTabs = MEDIA_TABS;

  protected readonly ColumnMode = ColumnMode;

  readonly totalPages = computed(() => Math.max(1, Math.ceil(this.total() / this.pageSize())));

  readonly canDelete = computed(() => {
    const role = this.auth.currentUser()?.role;
    return role ? hasPermission(role, PERMISSIONS.DELETE_POSTS) : false;
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

  setMediaTab(key: MediaTab): void {
    this.mediaTab.set(key);
    this.page.set(1);
    this.loadPosts();
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

  isVisualMedia(type: MediaType): boolean {
    return type === 'image' || type === 'video' || type === 'reel';
  }

  onRowActivate(event: { type: string; row?: Post }): void {
    if (event.type === 'click' && event.row) {
      this.openPostModal(event.row);
    }
  }

  openPostModal(post: Post): void {
    this.modalPost.set(post);
    this.postModalRef = this.modalService.show(this.postModalTpl, {
      class: 'modal-dialog-centered modal-lg',
    });
  }

  closePostModal(): void {
    this.postModalRef?.hide();
    this.modalPost.set(null);
  }

  async deletePost(post: Post, fromModal = false): Promise<void> {
    const confirmed = await this.confirm.confirmDanger(
      'Delete Post',
      'This will remove the post and all its comments. This cannot be undone.',
    );
    if (!confirmed) return;

    this.actionPostId.set(post.id);
    this.api
      .deletePost(post.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionPostId.set(null);
          this.toast.success('Post deleted');
          if (fromModal) this.closePostModal();
          this.loadPosts();
        },
        error: () => {
          this.actionPostId.set(null);
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

    const mediaType = this.mediaTab();
    if (mediaType) params['media_type'] = mediaType;

    this.api
      .getPosts(params)
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
          this.toast.error('Failed to load posts');
        },
      });
  }
}