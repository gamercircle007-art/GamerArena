import {
  ChangeDetectionStrategy,
  Component,
  inject,
  OnInit,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  bootstrapFlag,
  bootstrapGrid,
  bootstrapImage,
  bootstrapTrash,
} from '@ng-icons/bootstrap-icons';

import { MediaAssetItem } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';
import { ConfirmService } from '../../shared/services/confirm.service';

@Component({
  selector: 'app-dms-list',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [FormsModule, NgIcon, PageHeaderComponent, DateFormatPipe],
  providers: [provideIcons({ bootstrapImage, bootstrapGrid, bootstrapFlag, bootstrapTrash })],
  template: `
    <div class="dms-page">
      <app-page-header
        title="Media Library"
        subtitle="Centralized DMS — all images, videos, and documents"
        [breadcrumbs]="[{ label: 'Home', route: '/dashboard' }, { label: 'Media Library' }]" />

      @if (stats()) {
        <div class="stats-row">
          <div class="stat-card">
            <span class="stat-label">Total Assets</span>
            <span class="stat-value">{{ stats()!.total_count }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">Storage Used</span>
            <span class="stat-value">{{ stats()!.total_size_label }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">Flagged</span>
            <span class="stat-value text-danger">{{ stats()!.flagged_count }}</span>
          </div>
        </div>
      }

      <div class="filters card mb-3 p-3">
        <div class="row g-2">
          <div class="col-md-3">
            <select class="form-select" [(ngModel)]="typeFilter" (ngModelChange)="load()">
              <option value="">All Types</option>
              <option value="image">Images</option>
              <option value="video">Videos</option>
              <option value="document">Documents</option>
              <option value="audio">Audio</option>
            </select>
          </div>
          <div class="col-md-3">
            <input
              class="form-control"
              placeholder="Search filename..."
              [(ngModel)]="search"
              (keyup.enter)="load()" />
          </div>
          <div class="col-md-2">
            <button class="btn btn-primary w-100" (click)="load()">Apply</button>
          </div>
        </div>
      </div>

      <div class="asset-grid">
        @for (asset of assets(); track asset.id) {
          <div class="asset-card card">
            <div class="asset-thumb">
              @if (asset.asset_type === 'image') {
                <img [src]="asset.cdn_url" [alt]="asset.original_filename || 'image'" />
              } @else {
                <div class="asset-icon">{{ asset.asset_type }}</div>
              }
            </div>
            <div class="card-body p-2">
              <div class="filename">{{ asset.original_filename || 'Untitled' }}</div>
              <div class="meta">
                <span class="badge bg-secondary">{{ asset.asset_type }}</span>
                <span class="badge bg-light text-dark">{{ asset.file_size_label }}</span>
              </div>
              <div class="meta small text-muted">{{ asset.context }}</div>
              <div class="meta small">{{ asset.uploader_name || 'Unknown' }} · {{ asset.created_at | dateFormat }}</div>
              <div class="actions mt-2">
                <a class="btn btn-sm btn-outline-primary" [href]="asset.cdn_url" target="_blank">View</a>
                <button class="btn btn-sm btn-outline-warning" (click)="flag(asset)">
                  <ng-icon name="bootstrapFlag" size="14" />
                </button>
                <button class="btn btn-sm btn-outline-danger" (click)="remove(asset)">
                  <ng-icon name="bootstrapTrash" size="14" />
                </button>
              </div>
            </div>
          </div>
        } @empty {
          <p class="text-muted">No media assets found.</p>
        }
      </div>
    </div>
  `,
  styles: [
    `
      .stats-row {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 1rem;
      }
      .stat-card {
        background: #fff;
        border-radius: 8px;
        padding: 1rem;
        border: 1px solid #e8e8e8;
      }
      .stat-label {
        display: block;
        font-size: 0.8rem;
        color: #888;
      }
      .stat-value {
        font-size: 1.4rem;
        font-weight: 700;
      }
      .asset-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
        gap: 1rem;
      }
      .asset-thumb {
        height: 140px;
        background: #f5f5f5;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
      }
      .asset-thumb img {
        width: 100%;
        height: 100%;
        object-fit: cover;
      }
      .asset-icon {
        text-transform: uppercase;
        font-weight: 700;
        color: #7367f0;
      }
      .filename {
        font-weight: 600;
        font-size: 0.85rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .meta {
        margin-top: 4px;
        display: flex;
        gap: 4px;
        flex-wrap: wrap;
      }
      .actions {
        display: flex;
        gap: 6px;
      }
    `,
  ],
})
export class DmsListComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);

  assets = signal<MediaAssetItem[]>([]);
  stats = signal<{
    total_count: number;
    total_size_label: string;
    flagged_count: number;
  } | null>(null);

  typeFilter = '';
  search = '';

  ngOnInit(): void {
    this.load();
    this.api.getDmsStats().subscribe({
      next: s => this.stats.set(s),
      error: () => {},
    });
  }

  load(): void {
    this.api
      .getDmsAssets({
        type: this.typeFilter || undefined,
        search: this.search || undefined,
        page: 1,
        limit: 40,
      })
      .subscribe({
        next: res => this.assets.set(res.items),
        error: () => this.toast.error('Failed to load media library'),
      });
  }

  flag(asset: MediaAssetItem): void {
    this.api.flagDmsAsset(asset.id, !asset.is_flagged).subscribe({
      next: () => {
        this.toast.success(asset.is_flagged ? 'Unflagged' : 'Flagged');
        this.load();
      },
      error: () => this.toast.error('Failed to update flag'),
    });
  }

  async remove(asset: MediaAssetItem): Promise<void> {
    const ok = await this.confirm.confirm(
      'Delete asset?',
      'This permanently removes the file from S3 and the database.',
    );
    if (!ok) return;
    this.api.deleteDmsAsset(asset.id).subscribe({
      next: () => {
        this.toast.success('Asset deleted');
        this.load();
      },
      error: () => this.toast.error('Failed to delete asset'),
    });
  }
}