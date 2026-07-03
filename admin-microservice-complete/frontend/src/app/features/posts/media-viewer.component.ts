import {
  ChangeDetectionStrategy,
  Component,
  computed,
  input,
  signal,
} from '@angular/core';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  bootstrapChat,
  bootstrapGeoAlt,
  bootstrapHeart,
  bootstrapShop,
} from '@ng-icons/bootstrap-icons';

import { Post } from '../../core/models';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';

@Component({
  selector: 'app-media-viewer',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [NgIcon, DateFormatPipe],
  providers: [
    provideIcons({
      bootstrapShop,
      bootstrapHeart,
      bootstrapChat,
      bootstrapGeoAlt,
    }),
  ],
  template: `
    @if (post(); as p) {
      <div class="media-viewer">
        <div class="media-stage">
          @if (isVideo()) {
            <video
              class="media-video"
              [src]="p.media_urls[0]"
              controls
              playsinline
              preload="metadata">
              Your browser does not support video playback.
            </video>
          } @else if (p.media_urls.length) {
            <div id="mediaCarousel" class="carousel slide">
              <div class="carousel-inner">
                @for (url of p.media_urls; track url; let i = $index) {
                  <div class="carousel-item" [class.active]="carouselIndex() === i">
                    <img [src]="url" [alt]="'Media ' + (i + 1)" class="media-image" />
                  </div>
                }
              </div>
              @if (p.media_urls.length > 1) {
                <button
                  type="button"
                  class="carousel-control-prev"
                  (click)="prevSlide(p.media_urls.length)">
                  <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                  <span class="visually-hidden">Previous</span>
                </button>
                <button
                  type="button"
                  class="carousel-control-next"
                  (click)="nextSlide(p.media_urls.length)">
                  <span class="carousel-control-next-icon" aria-hidden="true"></span>
                  <span class="visually-hidden">Next</span>
                </button>
              }
            </div>
          } @else {
            <div class="text-only-stage">
              <p class="mb-0">{{ p.content }}</p>
            </div>
          }
        </div>

        <div class="media-meta">
          @if (isVideo() || p.media_urls.length) {
            <p class="content-text">{{ p.content }}</p>
          }

          <div class="meta-row">
            <div class="parlor-chip">
              <span class="parlor-avatar">
                <ng-icon name="bootstrapShop" size="14" />
              </span>
              <span class="fw-medium">{{ p.parlor?.name || 'Unknown Parlor' }}</span>
              @if (p.parlor?.is_verified) {
                <span class="badge bg-success-subtle text-success ms-1">Verified</span>
              }
            </div>
            <span class="text-muted small">{{ p.created_at | dateFormat }}</span>
          </div>

          <div class="stats-row">
            <span class="stat">
              <ng-icon name="bootstrapHeart" size="14" class="text-danger" />
              {{ formatCount(p.likes_count) }} likes
            </span>
            <span class="stat">
              <ng-icon name="bootstrapChat" size="14" class="text-primary" />
              {{ formatCount(p.comments_count) }} comments
            </span>
            <span class="media-type-badge" [class]="'type-' + p.media_type">
              {{ p.media_type }}
            </span>
          </div>

          @if (hasGeo()) {
            <div class="geo-section">
              <div class="geo-label">
                <ng-icon name="bootstrapGeoAlt" size="14" class="text-danger" />
                <span>{{ p.geo_lat }}, {{ p.geo_lng }}</span>
              </div>
              <a
                [href]="mapLink(p.geo_lat!, p.geo_lng!)"
                target="_blank"
                rel="noopener noreferrer"
                class="small text-primary">
                View location on map →
              </a>
            </div>
          }
        </div>
      </div>
    }
  `,
  styles: `
    .media-viewer { display: flex; flex-direction: column; gap: 1rem; }

    .media-stage {
      background: #f8f8f8;
      border-radius: 0.75rem;
      overflow: hidden;
      min-height: 200px;
    }

    .media-image,
    .media-video {
      width: 100%;
      max-height: 420px;
      object-fit: contain;
      display: block;
      background: #1e1e2d;
    }

    .text-only-stage {
      padding: 2rem 1.5rem;
      color: #5e5873;
      font-size: 0.9375rem;
      line-height: 1.6;
    }

    .content-text {
      color: #5e5873;
      font-size: 0.9375rem;
      line-height: 1.6;
      margin-bottom: 0.75rem;
    }

    .meta-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      flex-wrap: wrap;
      margin-bottom: 0.75rem;
    }

    .parlor-chip {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: #5e5873;
    }

    .parlor-avatar {
      width: 28px;
      height: 28px;
      border-radius: 0.375rem;
      background: rgba(115, 103, 240, 0.12);
      color: #7367f0;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .stats-row {
      display: flex;
      align-items: center;
      gap: 1rem;
      flex-wrap: wrap;
      margin-bottom: 0.75rem;
    }

    .stat {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.875rem;
      color: #6e6b7b;
    }

    .media-type-badge {
      display: inline-block;
      padding: 0.2rem 0.5rem;
      border-radius: 0.25rem;
      font-size: 0.6875rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }

    .type-text { background: #f3f2f7; color: #6e6b7b; }
    .type-image { background: rgba(0, 207, 232, 0.12); color: #00cfe8; }
    .type-video { background: rgba(115, 103, 240, 0.12); color: #7367f0; }
    .type-reel { background: rgba(234, 84, 85, 0.12); color: #ea5455; }

    .geo-section { margin-top: 0.5rem; }

    .geo-label {
      display: flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.8125rem;
      color: #6e6b7b;
      margin-bottom: 0.5rem;
    }

    .carousel-control-prev,
    .carousel-control-next {
      width: 10%;
    }
  `,
})
export class MediaViewerComponent {
  readonly post = input.required<Post>();

  readonly carouselIndex = signal(0);

  readonly isVideo = computed(() => {
    const type = this.post().media_type;
    return type === 'video' || type === 'reel';
  });

  readonly hasGeo = computed(() => {
    const p = this.post();
    return p.geo_lat != null && p.geo_lng != null;
  });

  prevSlide(total: number): void {
    const next = (this.carouselIndex() - 1 + total) % total;
    this.carouselIndex.set(next);
  }

  nextSlide(total: number): void {
    const next = (this.carouselIndex() + 1) % total;
    this.carouselIndex.set(next);
  }

  formatCount(value: number): string {
    if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
    return String(value);
  }

  mapLink(lat: number, lng: number): string {
    return `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lng}#map=15/${lat}/${lng}`;
  }
}