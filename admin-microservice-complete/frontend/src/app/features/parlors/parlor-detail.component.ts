import {
  ChangeDetectionStrategy,
  Component,
  computed,
  DestroyRef,
  inject,
  input,
  OnInit,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { DecimalPipe } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  bootstrapArrowLeft,
  bootstrapCheckCircle,
  bootstrapGeoAlt,
  bootstrapPeople,
  bootstrapShop,
  bootstrapStarFill,
  bootstrapTelephone,
  bootstrapTrash,
} from '@ng-icons/bootstrap-icons';
import { TabsModule } from 'ngx-bootstrap/tabs';

import { hasPermission, PERMISSIONS } from '../../core/constants/permissions';
import { ParlourEvent, Parlor, Rating } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { AuthService } from '../../core/services/auth.service';
import { MockDataService } from '../../core/services/mock-data.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { StatsCardComponent } from '../../shared/components/stats-card/stats-card.component';
import { StatusBadgeComponent } from '../../shared/components/status-badge/status-badge.component';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';
import { ConfirmService } from '../../shared/services/confirm.service';

@Component({
  selector: 'app-parlor-detail',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DecimalPipe,
    RouterLink,
    TabsModule,
    NgIcon,
    PageHeaderComponent,
    StatsCardComponent,
    StatusBadgeComponent,
    DateFormatPipe,
  ],
  providers: [
    provideIcons({
      bootstrapArrowLeft,
      bootstrapShop,
      bootstrapTelephone,
      bootstrapStarFill,
      bootstrapPeople,
      bootstrapCheckCircle,
      bootstrapGeoAlt,
      bootstrapTrash,
    }),
  ],
  template: `
    <div class="parlor-detail-page">
      @if (loading()) {
        <div class="loading-state">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
        </div>
      } @else if (loadError() || !parlor()) {
        <div class="card error-card">
          <div class="card-body text-center py-5">
            <p class="text-muted mb-3">Parlor not found or failed to load.</p>
            <div class="d-flex justify-content-center gap-2">
              <button type="button" class="btn btn-sm btn-primary" (click)="loadParlor()">
                Retry
              </button>
              <a routerLink="/parlors" class="btn btn-sm btn-light">← Back to Parlors</a>
            </div>
          </div>
        </div>
      } @else {
        @if (parlor(); as p) {
          <app-page-header
            [title]="p.name"
            [subtitle]="p.address || 'Parlor detail'"
            [breadcrumbs]="[
              { label: 'Home', route: '/dashboard' },
              { label: 'Parlors', route: '/parlors' },
              { label: p.name },
            ]">
            <a routerLink="/parlors" class="btn btn-sm btn-light">
              <ng-icon name="bootstrapArrowLeft" size="14" class="me-1" />
              Back to list
            </a>
            @if (canVerify() && !p.is_verified) {
              <button
                type="button"
                class="btn btn-sm btn-outline-success"
                [disabled]="actionLoading()"
                (click)="verifyParlor(true)">
                <ng-icon name="bootstrapCheckCircle" size="14" class="me-1" />
                Verify
              </button>
            }
            @if (canVerify() && p.is_verified) {
              <button
                type="button"
                class="btn btn-sm btn-outline-warning"
                [disabled]="actionLoading()"
                (click)="verifyParlor(false)">
                Unverify
              </button>
            }
            @if (canDelete()) {
              <button
                type="button"
                class="btn btn-sm btn-outline-danger"
                [disabled]="actionLoading()"
                (click)="deleteParlor()">
                <ng-icon name="bootstrapTrash" size="14" class="me-1" />
                Delete
              </button>
            }
          </app-page-header>

          <!-- Header Card -->
          <div class="card parlor-header-card mb-4">
            <div class="card-body">
              <div class="row g-4 align-items-start">
                <div class="col-auto">
                  <div class="parlor-logo">
                    @if (p.logo_url) {
                      <img [src]="p.logo_url" [alt]="p.name" />
                    } @else {
                      <ng-icon name="bootstrapShop" size="28" />
                    }
                  </div>
                </div>
                <div class="col">
                  <div class="d-flex align-items-center gap-2 flex-wrap mb-2">
                    <h5 class="mb-0 fw-bold">{{ p.name }}</h5>
                    @if (p.is_verified) {
                      <span class="verified-badge">
                        <ng-icon name="bootstrapCheckCircle" size="14" />
                        Verified
                      </span>
                    } @else {
                      <app-status-badge status="pending" />
                    }
                  </div>
                  <div class="row g-3">
                    <div class="col-md-6">
                      <div class="info-label">Address</div>
                      <div class="info-value">{{ p.address || '—' }}</div>
                    </div>
                    <div class="col-md-3">
                      <div class="info-label">Phone</div>
                      <div class="info-value d-flex align-items-center gap-2">
                        <ng-icon name="bootstrapTelephone" size="14" class="text-muted" />
                        {{ p.phone || ownerPhone() || '—' }}
                      </div>
                    </div>
                    <div class="col-md-3">
                      <div class="info-label">Rating</div>
                      <div class="info-value d-flex align-items-center gap-1">
                        @if (p.rating != null) {
                          <ng-icon name="bootstrapStarFill" size="14" class="text-warning" />
                          {{ p.rating | number: '1.1-1' }}
                        } @else {
                          —
                        }
                      </div>
                    </div>
                    <div class="col-md-3">
                      <div class="info-label">Followers</div>
                      <div class="info-value d-flex align-items-center gap-2">
                        <ng-icon name="bootstrapPeople" size="14" class="text-muted" />
                        {{ formatCount(p.follower_count) }}
                      </div>
                    </div>
                    @if (ownerName()) {
                      <div class="col-md-3">
                        <div class="info-label">Owner</div>
                        <div class="info-value">{{ ownerName() }}</div>
                      </div>
                    }
                    <div class="col-md-3">
                      <div class="info-label">Joined</div>
                      <div class="info-value">{{ p.created_at | dateFormat }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Tabs -->
          <div class="card tabs-card">
            <div class="card-body">
              <tabset>
                <tab heading="Overview">
                  <div class="tab-content-area">
                    <p class="description-text">{{ p.description || 'No description provided.' }}</p>
                    <div class="row g-3 g-xl-4 mb-4">
                      <div class="col-6 col-xl-3">
                        <app-stats-card
                          title="Followers"
                          [value]="formatCount(p.follower_count)"
                          icon="bootstrapPeople"
                          color="primary" />
                      </div>
                      <div class="col-6 col-xl-3">
                        <app-stats-card
                          title="Posts"
                          [value]="formatCount(p.post_count)"
                          icon="bootstrapShop"
                          color="info" />
                      </div>
                      <div class="col-6 col-xl-3">
                        <app-stats-card
                          title="Rating"
                          [value]="p.rating != null ? (p.rating | number: '1.1-1')! : '—'"
                          icon="bootstrapStarFill"
                          color="warning" />
                      </div>
                      <div class="col-6 col-xl-3">
                        <app-stats-card
                          title="Games"
                          [value]="p.game_types.length"
                          icon="bootstrapShop"
                          color="success" />
                      </div>
                    </div>
                    @if (p.latitude != null && p.longitude != null) {
                      <div class="coords-card">
                        <div class="coords-label">
                          <ng-icon name="bootstrapGeoAlt" size="16" class="text-danger" />
                          Location
                        </div>
                        <p class="mb-2 text-muted small">
                          {{ p.latitude }}, {{ p.longitude }}
                        </p>
                        <a
                          [href]="mapLink(p.latitude, p.longitude)"
                          target="_blank"
                          rel="noopener noreferrer"
                          class="btn btn-sm btn-outline-primary">
                          View on map
                        </a>
                      </div>
                    }
                  </div>
                </tab>

                <tab heading="Games">
                  <div class="tab-content-area">
                    <div class="games-grid">
                      @for (game of p.game_types; track game) {
                        <span class="game-chip">{{ game }}</span>
                      }
                      @if (!p.game_types.length) {
                        <span class="text-muted">No games listed</span>
                      }
                    </div>
                  </div>
                </tab>

                <tab heading="Time Slots">
                  <div class="tab-content-area">
                    @if (timeSlots().length) {
                      <div class="list-group list-group-flush">
                        @for (slot of timeSlots(); track slot.id) {
                          <div class="list-group-item px-0">
                            <div class="d-flex justify-content-between align-items-start gap-3">
                              <div>
                                <div class="fw-medium">{{ slot.label }}</div>
                                <small class="text-muted">
                                  {{ slot.game }} · {{ slot.start_time }} – {{ slot.end_time }}
                                </small>
                              </div>
                              <span class="badge bg-primary-subtle text-primary">
                                {{ slot.booked_slots }}/{{ slot.total_slots }} booked
                              </span>
                            </div>
                          </div>
                        }
                      </div>
                    } @else {
                      <div class="empty-tab">No time slots configured</div>
                    }
                  </div>
                </tab>

                <tab heading="Events">
                  <div class="tab-content-area">
                    @if (events().length) {
                      <div class="list-group list-group-flush">
                        @for (event of events(); track event.id) {
                          <div class="list-group-item px-0">
                            <div class="d-flex justify-content-between align-items-start gap-3">
                              <div>
                                <div class="fw-medium">{{ event.title }}</div>
                                <small class="text-muted">
                                  {{ event.event_type }} · {{ event.start_time | dateFormat }}
                                </small>
                              </div>
                              <app-status-badge [status]="event.status" />
                            </div>
                          </div>
                        }
                      </div>
                    } @else {
                      <div class="empty-tab">No events for this parlor</div>
                    }
                  </div>
                </tab>

                <tab heading="Gallery">
                  <div class="tab-content-area">
                    @if (gallery().length) {
                      <div class="gallery-grid">
                        @for (url of gallery(); track url) {
                          <div class="gallery-item">
                            <img [src]="url" alt="Gallery image" />
                          </div>
                        }
                      </div>
                    } @else {
                      <div class="empty-tab">No gallery images yet</div>
                    }
                  </div>
                </tab>

                <tab heading="Reviews">
                  <div class="tab-content-area">
                    @if (reviews().length) {
                      <div class="list-group list-group-flush">
                        @for (review of reviews(); track review.id) {
                          <div class="list-group-item px-0">
                            <div class="d-flex justify-content-between align-items-start gap-2 mb-1">
                              <span class="fw-medium">{{ review.user?.name || 'Anonymous' }}</span>
                              <span class="review-stars">
                                @for (star of starRange(review.rating); track $index) {
                                  <ng-icon
                                    name="bootstrapStarFill"
                                    size="12"
                                    [class.star-filled]="star"
                                    [class.star-empty]="!star" />
                                }
                              </span>
                            </div>
                            <p class="mb-1 small text-muted">{{ review.review || '—' }}</p>
                            <small class="text-muted">{{ review.created_at | dateFormat }}</small>
                          </div>
                        }
                      </div>
                    } @else {
                      <div class="empty-tab">No reviews yet</div>
                    }
                  </div>
                </tab>
              </tabset>
            </div>
          </div>
        }
      }
    </div>
  `,
  styles: `
    .loading-state {
      display: flex;
      justify-content: center;
      padding: 4rem 1rem;
    }

    .parlor-logo {
      width: 72px;
      height: 72px;
      border-radius: 0.75rem;
      background: linear-gradient(118deg, #7367f0, rgba(115, 103, 240, 0.7));
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }

    .parlor-logo img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .verified-badge {
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      padding: 0.25rem 0.625rem;
      border-radius: 0.375rem;
      font-size: 0.75rem;
      font-weight: 600;
      background: rgba(40, 199, 111, 0.12);
      color: #28c76f;
    }

    .info-label {
      font-size: 0.75rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: #b9b9c3;
      margin-bottom: 0.25rem;
    }

    .info-value {
      font-size: 0.9375rem;
      color: #5e5873;
      font-weight: 500;
    }

    .tabs-card .card-body { padding: 1.25rem 1.5rem; }

    .tab-content-area { padding-top: 1.25rem; }

    .description-text {
      color: #5e5873;
      font-size: 0.9375rem;
      line-height: 1.6;
      margin-bottom: 1.5rem;
    }

    .coords-card {
      padding: 1rem;
      border: 1px solid #ebe9f1;
      border-radius: 0.5rem;
      background: #fafafa;
    }

    .coords-label {
      display: flex;
      align-items: center;
      gap: 0.35rem;
      font-weight: 600;
      color: #5e5873;
      margin-bottom: 0.5rem;
    }

    .games-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .game-chip {
      display: inline-block;
      padding: 0.375rem 0.75rem;
      border-radius: 0.375rem;
      font-size: 0.8125rem;
      font-weight: 600;
      background: rgba(115, 103, 240, 0.1);
      color: #7367f0;
    }

    .gallery-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 0.75rem;
    }

    .gallery-item {
      aspect-ratio: 1;
      border-radius: 0.5rem;
      overflow: hidden;
      background: #f3f2f7;
    }

    .gallery-item img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .review-stars { display: flex; gap: 1px; }
    .star-filled { color: #ff9f43; }
    .star-empty { color: #d8d6de; }

    .empty-tab {
      padding: 2rem 1rem;
      text-align: center;
      color: #b9b9c3;
      font-size: 0.875rem;
    }
  `,
})
export class ParlorDetailComponent implements OnInit {
  readonly id = input.required<string>();

  private readonly api = inject(AdminApiService);
  private readonly auth = inject(AuthService);
  private readonly mock = inject(MockDataService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  readonly parlor = signal<Parlor | null>(null);
  readonly events = signal<ParlourEvent[]>([]);
  readonly reviews = signal<Rating[]>([]);
  readonly timeSlots = signal<ReturnType<MockDataService['getParlorTimeSlots']>>([]);
  readonly gallery = signal<string[]>([]);
  readonly loading = signal(true);
  readonly loadError = signal(false);
  readonly actionLoading = signal(false);

  readonly ownerName = computed(() => {
    const p = this.parlor();
    if (!p?.owner_id) return null;
    return this.mock.getOwnerInfo(p.owner_id)?.name ?? null;
  });

  readonly ownerPhone = computed(() => {
    const p = this.parlor();
    if (!p?.owner_id) return null;
    return this.mock.getOwnerInfo(p.owner_id)?.phone ?? null;
  });

  readonly canVerify = computed(() => {
    const role = this.auth.currentUser()?.role;
    return role ? hasPermission(role, PERMISSIONS.VERIFY_PARLORS) : false;
  });

  readonly canDelete = computed(() => {
    const role = this.auth.currentUser()?.role;
    return role ? hasPermission(role, PERMISSIONS.DELETE_PARLORS) : false;
  });

  ngOnInit(): void {
    this.loadParlor();
  }

  loadParlor(): void {
    this.loading.set(true);
    this.loadError.set(false);

    this.api
      .getParlor(this.id())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: parlor => {
          this.parlor.set(parlor);
          this.loading.set(false);
          this.loadTabData(parlor.id);
        },
        error: () => {
          this.loading.set(false);
          this.loadError.set(true);
          this.toast.error('Failed to load parlor');
        },
      });
  }

  formatCount(value: number): string {
    if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
    if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
    return String(value);
  }

  starRange(rating: number): boolean[] {
    const filled = Math.round(rating);
    return Array.from({ length: 5 }, (_, i) => i < filled);
  }

  mapLink(lat: number, lng: number): string {
    return `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lng}#map=15/${lat}/${lng}`;
  }

  async verifyParlor(isVerified: boolean): Promise<void> {
    const current = this.parlor();
    if (!current) return;

    if (!isVerified) {
      const confirmed = await this.confirm.confirm(
        'Unverify Parlor',
        `Remove verification from "${current.name}"?`,
        'Unverify',
        'warning',
      );
      if (!confirmed) return;
    }

    this.actionLoading.set(true);
    this.api
      .verifyParlor(current.id, isVerified)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: updated => {
          this.actionLoading.set(false);
          this.parlor.set(updated);
          this.toast.success(isVerified ? 'Parlor verified' : 'Parlor unverified');
        },
        error: () => {
          this.actionLoading.set(false);
          this.toast.error('Failed to update verification');
        },
      });
  }

  async deleteParlor(): Promise<void> {
    const current = this.parlor();
    if (!current) return;

    const confirmed = await this.confirm.confirmDanger(
      'Delete Parlor',
      `Permanently delete "${current.name}"? This cannot be undone.`,
    );
    if (!confirmed) return;

    this.actionLoading.set(true);
    this.api
      .deleteParlor(current.id)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.actionLoading.set(false);
          this.toast.success('Parlor deleted');
          this.router.navigate(['/parlors']);
        },
        error: () => {
          this.actionLoading.set(false);
          this.toast.error('Failed to delete parlor');
        },
      });
  }

  private loadTabData(parlorId: string): void {
    this.timeSlots.set(this.mock.getParlorTimeSlots(parlorId));
    this.gallery.set(this.mock.getParlorGallery(parlorId));

    this.api
      .getEvents({ parlor_id: parlorId, limit: 10 })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => this.events.set(res.items),
        error: () => this.events.set([]),
      });

    this.api
      .getRatings({ parlor_id: parlorId, limit: 10 })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => this.reviews.set(res.items),
        error: () => this.reviews.set([]),
      });
  }
}