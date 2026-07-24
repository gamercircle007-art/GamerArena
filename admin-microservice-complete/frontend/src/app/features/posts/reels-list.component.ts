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
import { RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  bootstrapHeart,
  bootstrapPlayFill,
  bootstrapShop,
  bootstrapTrash,
} from '@ng-icons/bootstrap-icons';
import { BsModalRef, BsModalService, ModalModule } from 'ngx-bootstrap/modal';

import { hasPermission, PERMISSIONS } from '../../core/constants/permissions';
import { Post } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { AuthService } from '../../core/services/auth.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { ConfirmService } from '../../shared/services/confirm.service';
import { MediaViewerComponent } from './media-viewer.component';

@Component({
  selector: 'app-reels-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [RouterLink, ModalModule, NgIcon, PageHeaderComponent, MediaViewerComponent],
  providers: [
    provideIcons({
      bootstrapPlayFill,
      bootstrapShop,
      bootstrapHeart,
      bootstrapTrash,
    }),
  ],
  template: `
    <div class="reels-page">
      <app-page-header
        title="Reels & Videos"
        subtitle="Short-form video content from parlors"
        [breadcrumbs]="[
          { label: 'Home', route: '/dashboard' },
          { label: 'Posts', route: '/posts' },
          { label: 'Reels' },
        ]">
        <a routerLink="/posts" class="btn btn-sm btn-light">All Posts</a>
      </app-page-header>

      @if (loadError()) {
        <div class="card">
          <div class="card-body text-center py-5">
            <p class="text-muted mb-3">Failed to load reels.</p>
            <button type="button" class="btn btn-sm btn-primary" (click)="loadReels()">
              Retry
            </button>
          </div>
        </div>
      } @else if (loading()) {
        <div class="loading-state">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
        </div>
      } @else if (!reels().length) {
        <div class="card">
          <div class="card-body empty-state">No reels found</div>
        </div>
      } @else {
        <div class="reels-grid">
          @for (reel of reels(); track reel.id) {
            <div class="reel-card card" (click)="openReelModal(reel)">
              <div class="reel-thumb">
                <video
                  class="reel-preview"
                  [src]="reel.media_urls[0]"
                  muted
                  playsinline
                  preload="metadata"></video>
                <div class="play-overlay">
                  <ng-icon name="bootstrapPlayFill" size="28" />
                </div>
              </div>
              <div class="card-body">
                <div class="d-flex align-items-center gap-2 mb-2">
                  <span class="parlor-avatar">
                    <ng-icon name="bootstrapShop" size="12" />
                  </span>
                  <span class="fw-medium small text-truncate">
                    {{ reel.parlor?.name || '—' }}
                  </span>
                </div>
                <p class="reel-caption small text-muted mb-2">{{ reel.content }}</p>
                <div class="d-flex align-items-center justify-content-between">
                  <span class="likes-count">
                    <ng-icon name="bootstrapHeart" size="12" class="text-danger" />
                    {{ formatCount(reel.likes_count) }}
                  </span>
                  @if (canDelete()) {
                    <button
                      type="button"
                      class="btn btn-sm btn-light delete-btn"
                      [disabled]="actionPostId() === reel.id"
                      (click)="deleteReel(reel, $event)">
                      <ng-icon name="bootstrapTrash" size="14" class="text-danger" />
                    </button>
                  }
                </div>
              </div>
            </div>
          }
        </div>
      }
    </div>

    <ng-template #reelModalTpl>
      @if (modalReel(); as reel) {
        <div class="modal-header border-0 pb-0">
          <h5 class="modal-title fw-bold">Reel</h5>
          <button type="button" class="btn-close" aria-label="Close" (click)="closeReelModal()"></button>
        </div>
        <div class="modal-body pt-2">
          <app-media-viewer [post]="reel" />
        </div>
        <div class="modal-footer border-0 pt-0">
          @if (canDelete()) {
            <button
              type="button"
              class="btn btn-outline-danger btn-sm"
              [disabled]="actionPostId() === reel.id"
              (click)="deleteReel(reel, $event, true)">
              Delete
            </button>
          }
          <button type="button" class="btn btn-light btn-sm" (click)="closeReelModal()">Close</button>
        </div>
      }
    </ng-template>
  `,
  styles: `
    .loading-state {
      display: flex;
      justify-content: center;
      padding: 4rem 1rem;
    }

    .reels-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1.25rem;
    }

    @media (max-width: 992px) {
      .reels-grid { grid-template-columns: repeat(2, 1fr); }
    }

    @media (max-width: 576px) {
      .reels-grid { grid-template-columns: 1fr; }
    }

    .reel-card {
      cursor: pointer;
      transition: transform 0.2s, box-shadow 0.2s;
      overflow: hidden;
    }

    .reel-card:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 24px rgba(115, 103, 240, 0.12);
    }

    .reel-thumb {
      position: relative;
      aspect-ratio: 9 / 16;
      max-height: 280px;
      background: #1e1e2d;
      overflow: hidden;
    }

    .reel-preview {
      width: 100%;
      height: 100%;
      object-fit: cover;
      pointer-events: none;
    }

    .play-overlay {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.35);
      color: #fff;
    }

    .parlor-avatar {
      width: 24px;
      height: 24px;
      border-radius: 0.25rem;
      background: rgba(115, 103, 240, 0.12);
      color: #7367f0;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .reel-caption {
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
      line-height: 1.4;
    }

    .likes-count {
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      font-size: 0.8125rem;
      color: #6e6b7b;
    }

    .delete-btn {
      border: 1px solid #ebe9f1;
      padding: 0.2rem 0.45rem;
    }

    .empty-state {
      padding: 2.5rem 1rem;
      text-align: center;
      color: #b9b9c3;
      font-size: 0.875rem;
    }
  `,
})
export class ReelsListComponent implements OnInit {
  @ViewChild('reelModalTpl') reelModalTpl!: TemplateRef<void>;

  private readonly api = inject(AdminApiService);
  private readonly auth = inject(AuthService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly modalService = inject(BsModalService);
  private readonly destroyRef = inject(DestroyRef);

  private reelModalRef?: BsModalRef;

  readonly reels = signal<Post[]>([]);
  readonly loading = signal(true);
  readonly loadError = signal(false);
  readonly actionPostId = signal<string | null>(null);
  readonly modalReel = signal<Post | null>(null);

  readonly canDelete = computed(() => {
    const role = this.auth.currentUser()?.role;
    return role ? hasPermission(role, PERMISSIONS.DELETE_POSTS) : false;
  });

  ngOnInit(): void {
    this.loadReels();
  }

  formatCount(value: number): string {
    if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
    return String(value);
  }

  openReelModal(reel: Post): void {
    this.modalReel.set(reel);
    this.reelModalRef = this.modalService.show(this.reelModalTpl, {
      class: 'modal-dialog-centered modal-lg',
    });
  }

  closeReelModal(): void {
    this.reelModalRef?.hide();
    this.modalReel.set(null);
  }

  async deleteReel(reel: Post, event: Event, fromModal = false): Promise<void> {
    event.stopPropagation();

    const confirmed = await this.confirm.confirmDanger(
      'Delete Reel',
      'This will permanently remove this reel.',
    );
    if (!confirmed) return;

    this.actionPostId.set(reel.id);
    this.api
      .deleteReel(reel.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionPostId.set(null);
          this.toast.success('Reel deleted');
          if (fromModal) this.closeReelModal();
          this.loadReels();
        },
        error: () => {
          this.actionPostId.set(null);
          this.toast.error('Failed to delete reel');
        },
      });
  }

  loadReels(): void {
    this.loading.set(true);
    this.loadError.set(false);

    this.api
      .getReels({ limit: 50 })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          // Map reel API shape → Post-like for existing template / media viewer
          const mapped: Post[] = res.items.map((r: Record<string, unknown>) => ({
            id: String(r['id']),
            content: String(r['caption'] ?? ''),
            media_urls: [String(r['video_url'] ?? r['thumbnail_url'] ?? '')].filter(Boolean),
            media_type: 'reel' as const,
            parlor_id: '',
            likes_count: Number(r['likes_count'] ?? 0),
            comments_count: Number(r['comments_count'] ?? 0),
            created_at: String(r['created_at'] ?? ''),
          }));
          this.reels.set(mapped);
          this.loading.set(false);
        },
        error: () => {
          // Fallback: posts filtered as reels
          this.api
            .getPosts({ media_type: 'reel', limit: 50 })
            .pipe(takeUntilDestroyed(this.destroyRef))
            .subscribe({
              next: res => {
                this.reels.set(res.items);
                this.loading.set(false);
              },
              error: () => {
                this.loading.set(false);
                this.loadError.set(true);
                this.toast.error('Failed to load reels');
              },
            });
        },
      });
  }
}