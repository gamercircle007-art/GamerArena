import { DecimalPipe } from '@angular/common';
import {
  AfterViewInit,
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  inject,
  OnInit,
  signal,
  ViewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NgIcon, provideIcons } from '@ng-icons/core';
import { bootstrapGeoAlt, bootstrapPerson } from '@ng-icons/bootstrap-icons';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';
import * as L from 'leaflet';

import { GeoActivity } from '../../core/models';
import { AdminApiService } from '../../core/services/admin-api.service';
import { ToastService } from '../../core/services/toast.service';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';
import { TruncatePipe } from '../../shared/pipes/truncate.pipe';

@Component({
  selector: 'app-geo-map',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    DecimalPipe,
    NgxDatatableModule,
    NgIcon,
    PageHeaderComponent,
    DateFormatPipe,
    TruncatePipe,
  ],
  providers: [provideIcons({ bootstrapPerson, bootstrapGeoAlt })],
  template: `
    <div class="geo-page">
      <app-page-header
        title="Geo Activity"
        subtitle="Track user post locations on the map"
        [breadcrumbs]="[
          { label: 'Home', route: '/dashboard' },
          { label: 'Geo Activity' },
        ]" />

      <div class="row g-4 geo-layout">
        <div class="col-lg-6">
          <div class="card table-card h-100">
            <div class="card-header bg-white border-bottom py-3">
              <h6 class="mb-0 fw-semibold">Recent Activity</h6>
            </div>
            <div class="card-body p-0">
              @if (loadError()) {
                <div class="error-state">
                  <p class="mb-2">Failed to load geo activity.</p>
                  <button type="button" class="btn btn-sm btn-primary" (click)="loadActivity()">
                    Retry
                  </button>
                </div>
              } @else {
                <ngx-datatable
                  class="bootstrap geo-table"
                  [rows]="rows()"
                  [columnMode]="ColumnMode.force"
                  [headerHeight]="44"
                  [rowHeight]="52"
                  [footerHeight]="0"
                  [scrollbarH]="true"
                  [loadingIndicator]="loading()"
                  [rowClass]="getRowClass"
                  (activate)="onRowActivate($event)">
                  <ngx-datatable-column name="User" [flexGrow]="1.5" [sortable]="false">
                    <ng-template let-row="row" ngx-datatable-cell-template>
                      <div class="d-flex align-items-center gap-2">
                        <ng-icon name="bootstrapPerson" size="16" class="text-muted" />
                        <span class="fw-medium">{{ row.user?.name || 'Unknown' }}</span>
                      </div>
                    </ng-template>
                  </ngx-datatable-column>

                  <ngx-datatable-column name="Location" [flexGrow]="1.5" [sortable]="false">
                    <ng-template let-row="row" ngx-datatable-cell-template>
                      <span class="coords-text">
                        <ng-icon name="bootstrapGeoAlt" size="12" class="me-1" />
                        {{ row.latitude | number: '1.4-4' }}, {{ row.longitude | number: '1.4-4' }}
                      </span>
                    </ng-template>
                  </ngx-datatable-column>

                  <ngx-datatable-column name="Post Preview" [flexGrow]="2" [sortable]="false">
                    <ng-template let-row="row" ngx-datatable-cell-template>
                      <span class="text-muted small">{{ row.post_preview || '—' | truncate: 50 }}</span>
                    </ng-template>
                  </ngx-datatable-column>

                  <ngx-datatable-column name="Date" [flexGrow]="1.2" [sortable]="false">
                    <ng-template let-row="row" ngx-datatable-cell-template>
                      {{ row.created_at | dateFormat }}
                    </ng-template>
                  </ngx-datatable-column>
                </ngx-datatable>

                @if (!loading() && !rows().length) {
                  <div class="empty-state">No geo activity found</div>
                }
              }
            </div>
          </div>
        </div>

        <div class="col-lg-6">
          <div class="card map-card h-100">
            <div class="card-header bg-white border-bottom py-3">
              <h6 class="mb-0 fw-semibold">Map View</h6>
              @if (selectedRow()) {
                <small class="text-muted">
                  {{ selectedRow()!.user?.name }} — {{ selectedRow()!.latitude | number: '1.4-4' }},
                  {{ selectedRow()!.longitude | number: '1.4-4' }}
                </small>
              }
            </div>
            <div class="card-body p-0">
              <div #mapContainer class="map-container"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: `
    .geo-layout { min-height: 400px; }

    .map-container {
      width: 100%;
      min-height: 300px;
      height: 100%;
    }

    .map-card .card-body { min-height: 300px; }

    .coords-text {
      font-size: 0.8125rem;
      font-family: ui-monospace, monospace;
      color: #6e6b7b;
    }

    :host ::ng-deep .geo-row--active {
      background-color: rgba(115, 103, 240, 0.08) !important;
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
export class GeoMapComponent implements OnInit, AfterViewInit {
  @ViewChild('mapContainer') mapContainer!: ElementRef<HTMLDivElement>;

  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  private map?: L.Map;
  private markersLayer?: L.LayerGroup;
  private markerById = new Map<string, L.CircleMarker>();
  private mapReady = false;
  private pendingRows: GeoActivity[] = [];

  readonly rows = signal<GeoActivity[]>([]);
  readonly loading = signal(false);
  readonly loadError = signal(false);
  readonly selectedRow = signal<GeoActivity | null>(null);

  protected readonly ColumnMode = ColumnMode;

  readonly getRowClass = (row: GeoActivity): string =>
    this.selectedRow()?.id === row.id ? 'geo-row--active' : '';

  ngOnInit(): void {
    this.loadActivity();
  }

  ngAfterViewInit(): void {
    this.initMap();
    this.mapReady = true;
    if (this.pendingRows.length) {
      this.renderMarkers(this.pendingRows);
      this.pendingRows = [];
    }
  }

  onRowActivate(event: { type: string; row?: GeoActivity }): void {
    if (event.type !== 'click' || !event.row) return;
    this.selectRow(event.row);
  }

  selectRow(row: GeoActivity): void {
    this.selectedRow.set(row);
    this.centerOnRow(row);
  }

  loadActivity(): void {
    this.loading.set(true);
    this.loadError.set(false);

    this.api
      .getGeoActivity({ page: 1, limit: 100 })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.rows.set(res.items);
          this.loading.set(false);
          this.updateMapMarkers(res.items);
          if (res.items.length) {
            this.selectRow(res.items[0]);
          }
        },
        error: () => {
          this.loading.set(false);
          this.loadError.set(true);
          this.toast.error('Failed to load geo activity');
        },
      });
  }

  private initMap(): void {
    this.map = L.map(this.mapContainer.nativeElement, {
      center: [12.9716, 77.5946],
      zoom: 11,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(this.map);

    this.markersLayer = L.layerGroup().addTo(this.map);
  }

  private updateMapMarkers(items: GeoActivity[]): void {
    if (!this.mapReady) {
      this.pendingRows = items;
      return;
    }
    this.renderMarkers(items);
  }

  private renderMarkers(items: GeoActivity[]): void {
    if (!this.map || !this.markersLayer) return;

    this.markersLayer.clearLayers();
    this.markerById.clear();

    const bounds: L.LatLngTuple[] = [];

    for (const item of items) {
      const latLng: L.LatLngTuple = [item.latitude, item.longitude];
      const marker = L.circleMarker(latLng, {
        radius: 8,
        fillColor: '#7367f0',
        color: '#fff',
        weight: 2,
        fillOpacity: 0.9,
      });

      marker.bindPopup(
        `<strong>${item.user?.name ?? 'User'}</strong><br/>${item.post_preview ?? 'No preview'}`,
      );
      marker.on('click', () => this.selectRow(item));
      marker.addTo(this.markersLayer);
      this.markerById.set(item.id, marker);
      bounds.push(latLng);
    }

    if (bounds.length > 1) {
      this.map.fitBounds(L.latLngBounds(bounds), { padding: [24, 24] });
    } else if (bounds.length === 1) {
      this.map.setView(bounds[0], 13);
    }

    setTimeout(() => this.map?.invalidateSize(), 100);
  }

  private centerOnRow(row: GeoActivity): void {
    if (!this.map) return;

    this.map.setView([row.latitude, row.longitude], 14, { animate: true });

    const marker = this.markerById.get(row.id);
    marker?.openPopup();
  }
}