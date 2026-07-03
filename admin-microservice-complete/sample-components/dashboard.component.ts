// sample-components/dashboard.component.ts
// COMPLETE DASHBOARD — stat cards, ng2-charts, ngx-datatable mini table.
// Use as reference pattern for the full dashboard build.

import { Component, signal, inject, OnInit, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData, ChartType } from 'chart.js';
import { NgIconsModule } from '@ng-icons/core';
import { NgxDatatableModule, ColumnMode } from '@swimlane/ngx-datatable';
import { AdminApiService } from '../../core/services/admin-api.service';
import { StatsCardComponent } from '../../shared/components/stats-card/stats-card.component';
import { AdminStats, AnalyticsData } from '../../core/models';

type Period = '7d' | '30d' | '90d';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, RouterLink, BaseChartDirective, NgIconsModule, NgxDatatableModule, StatsCardComponent],
  template: `
    <div class="dashboard-wrapper">

      <!-- KPI Cards Row 1 -->
      <div class="row g-4 mb-4">
        <div class="col-6 col-xl-3">
          <app-stats-card title="Total Users" [value]="stats()?.total_users ?? 0"
            icon="bootstrapPeople" color="primary"
            [subtitle]="'+' + (stats()?.new_users_today ?? 0) + ' today'" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card title="Total Parlors" [value]="stats()?.total_parlors ?? 0"
            icon="bootstrapShop" color="success"
            [subtitle]="(stats()?.pending_verification ?? 0) + ' pending verify'" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card title="Active Tournaments" [value]="stats()?.active_tournaments ?? 0"
            icon="bootstrapTrophy" color="warning"
            [subtitle]="(stats()?.total_tournaments ?? 0) + ' total'" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card title="Today's Bookings" [value]="stats()?.new_bookings_today ?? 0"
            icon="bootstrapTicketPerforated" color="danger"
            [subtitle]="(stats()?.total_bookings ?? 0) + ' all time'" />
        </div>
      </div>

      <!-- KPI Cards Row 2 -->
      <div class="row g-4 mb-4">
        <div class="col-6 col-xl-3">
          <app-stats-card title="Total Posts" [value]="stats()?.total_posts ?? 0"
            icon="bootstrapFileText" color="info" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card title="Total Events" [value]="stats()?.total_events ?? 0"
            icon="bootstrapCalendarEvent" color="warning" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card title="Community Posts" [value]="stats()?.total_community_posts ?? 0"
            icon="bootstrapGlobe2" color="success" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card title="Total Ratings" [value]="stats()?.total_ratings ?? 0"
            icon="bootstrapStar" color="primary" />
        </div>
      </div>

      <!-- Period Selector -->
      <div class="d-flex justify-content-between align-items-center mb-4">
        <h5 class="fw-bold text-dark mb-0">Platform Analytics</h5>
        <div class="btn-group btn-group-sm" role="group">
          @for (p of periods; track p) {
            <button type="button" class="btn"
              [class.btn-primary]="activePeriod() === p"
              [class.btn-outline-primary]="activePeriod() !== p"
              (click)="setPeriod(p)">{{ p }}</button>
          }
        </div>
      </div>

      <!-- Charts Row 1 -->
      <div class="row g-4 mb-4">
        <div class="col-xl-7">
          <div class="card shadow-sm h-100">
            <div class="card-header bg-white border-bottom-0 pt-4 pb-0">
              <h6 class="card-title fw-bold text-dark mb-0">User Growth</h6>
              <small class="text-muted">Daily new signups</small>
            </div>
            <div class="card-body">
              @if (analytics()) {
                <canvas baseChart
                  [data]="userGrowthData()"
                  [options]="lineChartOptions"
                  [type]="'line'">
                </canvas>
              } @else {
                <div class="chart-skeleton"></div>
              }
            </div>
          </div>
        </div>
        <div class="col-xl-5">
          <div class="card shadow-sm h-100">
            <div class="card-header bg-white border-bottom-0 pt-4 pb-0">
              <h6 class="card-title fw-bold text-dark mb-0">Daily Bookings</h6>
            </div>
            <div class="card-body">
              @if (analytics()) {
                <canvas baseChart
                  [data]="bookingsData()"
                  [options]="barChartOptions"
                  [type]="'bar'">
                </canvas>
              } @else {
                <div class="chart-skeleton"></div>
              }
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Row 2 -->
      <div class="row g-4 mb-4">
        <div class="col-xl-5">
          <div class="card shadow-sm h-100">
            <div class="card-header bg-white border-bottom-0 pt-4 pb-0">
              <h6 class="card-title fw-bold text-dark mb-0">Game Distribution</h6>
            </div>
            <div class="card-body d-flex align-items-center justify-content-center">
              @if (analytics()) {
                <canvas baseChart
                  [data]="gameDistributionData()"
                  [options]="pieChartOptions"
                  [type]="'doughnut'">
                </canvas>
              } @else {
                <div class="chart-skeleton rounded-circle" style="width:200px;height:200px"></div>
              }
            </div>
          </div>
        </div>
        <div class="col-xl-7">
          <div class="card shadow-sm h-100">
            <div class="card-header bg-white border-bottom-0 pt-4 pb-0">
              <h6 class="card-title fw-bold text-dark mb-0">Top Parlors by Bookings</h6>
            </div>
            <div class="card-body p-0">
              @if (analytics()) {
                @for (parlor of analytics()!.top_parlors.slice(0, 6); track parlor.parlor_id; let i = $index) {
                  <div class="top-parlor-row px-4 py-3 border-bottom">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                      <span class="fw-medium text-dark fs-sm">
                        {{ i + 1 }}. {{ parlor.parlor_name }}
                      </span>
                      <span class="text-muted fs-sm">{{ parlor.bookings_count }} bookings</span>
                    </div>
                    <div class="progress" style="height:6px">
                      <div class="progress-bar bg-primary" role="progressbar"
                        [style.width]="getBarWidth(parlor.bookings_count) + '%'">
                      </div>
                    </div>
                  </div>
                }
                @if (!analytics()?.top_parlors?.length) {
                  <div class="text-center text-muted py-5">No booking data yet</div>
                }
              } @else {
                @for (_ of [1,2,3,4,5]; track $index) {
                  <div class="px-4 py-3 border-bottom">
                    <div class="skeleton-line mb-2"></div>
                    <div class="skeleton-line" style="width:80%;height:6px"></div>
                  </div>
                }
              }
            </div>
          </div>
        </div>
      </div>

      <!-- Pending Verification Alert -->
      @if ((stats()?.pending_verification ?? 0) > 0) {
        <div class="alert alert-warning d-flex align-items-center gap-3 mb-4">
          <ng-icon name="bootstrapExclamationTriangle" size="20" />
          <div>
            <strong>{{ stats()!.pending_verification }} Parlor(s) awaiting verification.</strong>
            <a routerLink="/parlors" [queryParams]="{filter:'unverified'}" class="ms-2">Review now →</a>
          </div>
        </div>
      }

    </div>
  `,
  styles: [`
    .chart-skeleton { background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 8px; height: 220px; }
    .skeleton-line { background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; border-radius: 4px; height: 12px; }
    @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
    .top-parlor-row:last-child { border-bottom: none !important; }
    .fs-sm { font-size: 13px; }
  `],
})
export class DashboardComponent implements OnInit {
  private api = inject(AdminApiService);

  stats     = signal<AdminStats | null>(null);
  analytics = signal<AnalyticsData | null>(null);
  activePeriod = signal<Period>('30d');
  periods: Period[] = ['7d', '30d', '90d'];

  protected ColumnMode = ColumnMode;

  // ── Chart configs ────────────────────────────────────────────────────────
  lineChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { maxTicksLimit: 8, font: { size: 11 } } },
      y: { grid: { color: '#f0f0f0' }, ticks: { font: { size: 11 } } },
    },
    elements: { line: { tension: 0.4 }, point: { radius: 3 } },
  };

  barChartOptions: ChartConfiguration['options'] = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: { x: { grid: { display: false } }, y: { grid: { color: '#f0f0f0' } } },
  };

  pieChartOptions: ChartConfiguration['options'] = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { position: 'right' } },
  };

  // Computed chart data from signals
  userGrowthData = computed<ChartData<'line'>>(() => ({
    labels: this.analytics()?.users_growth?.map(d => d.date.slice(5)) ?? [],
    datasets: [{
      data: this.analytics()?.users_growth?.map(d => d.count) ?? [],
      label: 'New Users',
      fill: true,
      backgroundColor: 'rgba(115,103,240,0.1)',
      borderColor: '#7367f0',
      borderWidth: 2,
      pointBackgroundColor: '#7367f0',
    }],
  }));

  bookingsData = computed<ChartData<'bar'>>(() => ({
    labels: this.analytics()?.bookings_per_day?.map(d => d.date.slice(5)) ?? [],
    datasets: [{
      data: this.analytics()?.bookings_per_day?.map(d => d.count) ?? [],
      label: 'Bookings',
      backgroundColor: 'rgba(40,199,111,0.8)',
      borderRadius: 4,
    }],
  }));

  gameDistributionData = computed<ChartData<'doughnut'>>(() => ({
    labels: this.analytics()?.game_type_distribution?.map(d => d.name) ?? [],
    datasets: [{
      data: this.analytics()?.game_type_distribution?.map(d => d.value) ?? [],
      backgroundColor: ['#7367f0','#28c76f','#ff9f43','#ea5455','#00cfe8','#82868b'],
    }],
  }));

  ngOnInit() {
    this.loadStats();
    this.loadAnalytics();
  }

  loadStats() {
    this.api.getStats().subscribe(data => this.stats.set(data));
  }

  loadAnalytics() {
    this.analytics.set(null);
    this.api.getAnalytics(this.activePeriod()).subscribe(data => this.analytics.set(data));
  }

  setPeriod(period: Period) {
    this.activePeriod.set(period);
    this.loadAnalytics();
  }

  getBarWidth(count: number): number {
    const max = Math.max(...(this.analytics()?.top_parlors?.map(p => p.bookings_count) ?? [1]));
    return max > 0 ? (count / max) * 100 : 0;
  }
}
