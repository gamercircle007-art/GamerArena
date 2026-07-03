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
  bootstrapBarChart,
  bootstrapCalendarCheck,
  bootstrapCurrencyRupee,
  bootstrapDownload,
  bootstrapGraphDownArrow,
  bootstrapGraphUpArrow,
  bootstrapPeople,
  bootstrapPersonPlus,
} from '@ng-icons/bootstrap-icons';
import { ChartConfiguration, ChartData } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';

import { AdminApiService } from '../../core/services/admin-api.service';
import { ToastService } from '../../core/services/toast.service';
import { AnalyticsData, ParlorRevenueStat, ParlorStat } from '../../core/models';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { StatsCardComponent } from '../../shared/components/stats-card/stats-card.component';
import { CurrencyInPipe } from '../../shared/pipes/currency-in.pipe';

type Period = '7d' | '30d' | '90d';

@Component({
  selector: 'app-analytics',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    BaseChartDirective,
    NgxDatatableModule,
    NgIcon,
    PageHeaderComponent,
    StatsCardComponent,
    CurrencyInPipe,
  ],
  providers: [
    provideIcons({
      bootstrapPeople,
      bootstrapPersonPlus,
      bootstrapCalendarCheck,
      bootstrapCurrencyRupee,
      bootstrapBarChart,
      bootstrapDownload,
      bootstrapGraphUpArrow,
      bootstrapGraphDownArrow,
    }),
  ],
  template: `
    <div class="analytics-page">
      <app-page-header
        title="Analytics"
        subtitle="Platform growth and revenue insights"
        [breadcrumbs]="[{ label: 'Home', route: '/dashboard' }, { label: 'Analytics' }]">
        <div class="d-flex align-items-center gap-2 flex-wrap">
          <div class="btn-group btn-group-sm period-selector" role="group" aria-label="Analytics period">
            @for (p of periods; track p) {
              <button
                type="button"
                class="btn"
                [class.btn-primary]="activePeriod() === p"
                [class.btn-outline-primary]="activePeriod() !== p"
                (click)="setPeriod(p)">
                {{ periodLabels[p] }}
              </button>
            }
          </div>
          <button
            type="button"
            class="btn btn-sm btn-outline-secondary d-inline-flex align-items-center gap-1"
            [disabled]="!analytics()"
            (click)="exportCsv()">
            <ng-icon name="bootstrapDownload" size="14" />
            Export CSV
          </button>
        </div>
      </app-page-header>

      @if (loadError()) {
        <div class="alert alert-danger d-flex align-items-center justify-content-between">
          <span>Failed to load analytics data.</span>
          <button type="button" class="btn btn-sm btn-danger" (click)="loadAnalytics()">Retry</button>
        </div>
      }

      <!-- KPI Row -->
      <div class="row g-3 g-xl-4 mb-4">
        <div class="col-6 col-xl-3">
          <app-stats-card
            title="Total Users"
            [value]="formatNumber(analytics()?.total_users)"
            icon="bootstrapPeople"
            color="primary" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card
            title="New This Period"
            [value]="formatNumber(analytics()?.new_users)"
            icon="bootstrapPersonPlus"
            color="success"
            [subtitle]="periodLabels[activePeriod()]" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card
            title="Total Bookings"
            [value]="formatNumber(analytics()?.total_bookings)"
            icon="bootstrapCalendarCheck"
            color="info" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card
            title="Revenue"
            [value]="analytics()?.revenue | currencyIn"
            icon="bootstrapCurrencyRupee"
            color="warning"
            [subtitle]="periodLabels[activePeriod()]" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card
            title="Conversion Rate"
            [value]="formatPercent(analytics()?.conversion_rate)"
            icon="bootstrapGraphUpArrow"
            color="success"
            [subtitle]="periodLabels[activePeriod()]" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card
            title="Cancellation Rate"
            [value]="formatPercent(analytics()?.cancellation_rate)"
            icon="bootstrapGraphDownArrow"
            color="danger"
            [subtitle]="periodLabels[activePeriod()]" />
        </div>
      </div>

      <!-- User Growth -->
      <div class="card chart-card mb-4">
        <div class="card-header border-0 bg-white">
          <h6 class="mb-0 fw-bold">User Growth</h6>
          <small class="text-muted">New signups per day — {{ periodLabels[activePeriod()] }}</small>
        </div>
        <div class="card-body">
          @if (analytics()) {
            <div class="chart-container">
              <canvas baseChart [data]="userGrowthData()" [options]="lineChartOptions" type="line"></canvas>
            </div>
          } @else {
            <div class="chart-skeleton"></div>
          }
        </div>
      </div>

      <!-- Bookings + Revenue -->
      <div class="row g-3 g-xl-4 mb-4">
        <div class="col-xl-6">
          <div class="card chart-card h-100">
            <div class="card-header border-0 bg-white">
              <h6 class="mb-0 fw-bold">Bookings per Day</h6>
              <small class="text-muted">Tournament + gaming slot bookings</small>
            </div>
            <div class="card-body">
              @if (analytics()) {
                <div class="chart-container">
                  <canvas baseChart [data]="bookingsData()" [options]="barChartOptions" type="bar"></canvas>
                </div>
              } @else {
                <div class="chart-skeleton"></div>
              }
            </div>
          </div>
        </div>
        <div class="col-xl-6">
          <div class="card chart-card h-100">
            <div class="card-header border-0 bg-white">
              <h6 class="mb-0 fw-bold">Revenue per Day</h6>
              <small class="text-muted">Daily platform revenue — {{ periodLabels[activePeriod()] }}</small>
            </div>
            <div class="card-body">
              @if (analytics()) {
                <div class="chart-container">
                  <canvas baseChart [data]="revenueData()" [options]="revenueChartOptions" type="line"></canvas>
                </div>
              } @else {
                <div class="chart-skeleton"></div>
              }
            </div>
          </div>
        </div>
      </div>

      <!-- Posts + Game Distribution -->
      <div class="row g-3 g-xl-4 mb-4">
        <div class="col-xl-6">
          <div class="card chart-card h-100">
            <div class="card-header border-0 bg-white">
              <h6 class="mb-0 fw-bold">Posts per Day</h6>
              <small class="text-muted">Social feed activity</small>
            </div>
            <div class="card-body">
              @if (analytics()) {
                <div class="chart-container">
                  <canvas baseChart [data]="postsData()" [options]="postsLineOptions" type="line"></canvas>
                </div>
              } @else {
                <div class="chart-skeleton"></div>
              }
            </div>
          </div>
        </div>
        <div class="col-xl-6">
          <div class="card chart-card h-100">
            <div class="card-header border-0 bg-white">
              <h6 class="mb-0 fw-bold">Game Distribution</h6>
              <small class="text-muted">Games across all parlors</small>
            </div>
            <div class="card-body d-flex align-items-center justify-content-center">
              @if (analytics()) {
                <div class="chart-container chart-container--doughnut">
                  <canvas
                    baseChart
                    [data]="gameDistributionData()"
                    [options]="doughnutChartOptions"
                    type="doughnut">
                  </canvas>
                </div>
              } @else {
                <div class="chart-skeleton chart-skeleton--circle"></div>
              }
            </div>
          </div>
        </div>
      </div>

      <!-- Top Parlors Tables -->
      <div class="row g-3 g-xl-4">
        <div class="col-xl-6">
          <div class="card table-card h-100">
            <div class="card-header border-0 bg-white">
              <h6 class="mb-0 fw-bold">Top Parlors by Bookings</h6>
              <small class="text-muted">{{ periodLabels[activePeriod()] }}</small>
            </div>
            <div class="card-body p-0">
              <ngx-datatable
                class="bootstrap analytics-table"
                [rows]="topParlors()"
                [columnMode]="ColumnMode.force"
                [headerHeight]="48"
                [rowHeight]="52"
                [footerHeight]="0"
                [scrollbarH]="true"
                [limit]="10">
                <ngx-datatable-column name="Parlor" prop="parlor_name" [flexGrow]="2">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    <span class="fw-medium">{{ row.parlor_name }}</span>
                  </ng-template>
                </ngx-datatable-column>
                <ngx-datatable-column name="Bookings" [flexGrow]="2">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    <div class="progress-cell">
                      <div class="progress mini-progress">
                        <div
                          class="progress-bar"
                          role="progressbar"
                          [style.width.%]="bookingPercent(row)"
                          [attr.aria-valuenow]="row.bookings_count"
                          aria-valuemin="0"
                          [attr.aria-valuemax]="maxBookings()">
                        </div>
                      </div>
                      <span class="progress-label">{{ row.bookings_count }}</span>
                    </div>
                  </ng-template>
                </ngx-datatable-column>
                <ngx-datatable-column name="Share" [flexGrow]="1">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    <span class="text-muted small">{{ bookingPercent(row) }}%</span>
                  </ng-template>
                </ngx-datatable-column>
              </ngx-datatable>
              @if (analytics() && !topParlors().length) {
                <div class="empty-state">No parlor data yet</div>
              }
            </div>
          </div>
        </div>
        <div class="col-xl-6">
          <div class="card table-card h-100">
            <div class="card-header border-0 bg-white">
              <h6 class="mb-0 fw-bold">Top Parlors by Revenue</h6>
              <small class="text-muted">{{ periodLabels[activePeriod()] }}</small>
            </div>
            <div class="card-body p-0">
              <ngx-datatable
                class="bootstrap analytics-table"
                [rows]="topParlorsByRevenue()"
                [columnMode]="ColumnMode.force"
                [headerHeight]="48"
                [rowHeight]="52"
                [footerHeight]="0"
                [scrollbarH]="true"
                [limit]="10">
                <ngx-datatable-column name="Parlor" prop="parlor_name" [flexGrow]="2">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    <span class="fw-medium">{{ row.parlor_name }}</span>
                  </ng-template>
                </ngx-datatable-column>
                <ngx-datatable-column name="Revenue" [flexGrow]="2">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    <div class="progress-cell">
                      <div class="progress mini-progress revenue-progress">
                        <div
                          class="progress-bar"
                          role="progressbar"
                          [style.width.%]="revenuePercent(row)"
                          [attr.aria-valuenow]="row.revenue"
                          aria-valuemin="0"
                          [attr.aria-valuemax]="maxRevenue()">
                        </div>
                      </div>
                      <span class="progress-label">{{ row.revenue | currencyIn }}</span>
                    </div>
                  </ng-template>
                </ngx-datatable-column>
                <ngx-datatable-column name="Share" [flexGrow]="1">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    <span class="text-muted small">{{ revenuePercent(row) }}%</span>
                  </ng-template>
                </ngx-datatable-column>
              </ngx-datatable>
              @if (analytics() && !topParlorsByRevenue().length) {
                <div class="empty-state">No revenue data yet</div>
              }
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: `
    .analytics-page { padding-bottom: 0.5rem; }

    .period-selector .btn {
      min-width: 72px;
      font-size: 0.8125rem;
      font-weight: 600;
    }

    .chart-card .card-header,
    .table-card .card-header { padding: 1.25rem 1.5rem 0.5rem; }

    .chart-container {
      position: relative;
      height: 260px;
      width: 100%;
    }

    .chart-container--doughnut {
      height: 240px;
      max-width: 360px;
      margin: 0 auto;
    }

    .chart-skeleton {
      height: 260px;
      border-radius: 8px;
      background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%);
      background-size: 200% 100%;
      animation: shimmer 1.5s infinite;
    }

    .chart-skeleton--circle {
      width: 200px;
      height: 200px;
      border-radius: 50%;
      margin: 0 auto;
    }

    .analytics-table { box-shadow: none; }

    .progress-cell {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .mini-progress {
      flex: 1;
      height: 6px;
      background: #f3f2f7;
      border-radius: 3px;
    }

    .mini-progress .progress-bar {
      background: linear-gradient(90deg, #7367f0, rgba(115, 103, 240, 0.7));
      border-radius: 3px;
    }

    .revenue-progress .progress-bar {
      background: linear-gradient(90deg, #ff9f43, rgba(255, 159, 67, 0.7));
    }

    .progress-label {
      font-weight: 600;
      font-size: 0.8125rem;
      min-width: 2.5rem;
      text-align: right;
      font-variant-numeric: tabular-nums;
    }

    .empty-state {
      padding: 2.5rem 1rem;
      text-align: center;
      color: #b9b9c3;
      font-size: 0.875rem;
    }

    @keyframes shimmer {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }
  `,
})
export class AnalyticsComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly destroyRef = inject(DestroyRef);

  readonly analytics = signal<AnalyticsData | null>(null);
  readonly activePeriod = signal<Period>('30d');
  readonly loadError = signal(false);

  readonly periods: Period[] = ['7d', '30d', '90d'];
  readonly periodLabels: Record<Period, string> = {
    '7d': '7 Days',
    '30d': '30 Days',
    '90d': '90 Days',
  };

  protected readonly ColumnMode = ColumnMode;

  readonly topParlors = computed(() => this.analytics()?.top_parlors?.slice(0, 10) ?? []);
  readonly topParlorsByRevenue = computed(
    () => this.analytics()?.top_parlors_by_revenue?.slice(0, 10) ?? [],
  );

  readonly maxBookings = computed(() => {
    const parlors = this.topParlors();
    if (!parlors.length) return 1;
    return Math.max(...parlors.map(p => p.bookings_count), 1);
  });

  readonly maxRevenue = computed(() => {
    const parlors = this.topParlorsByRevenue();
    if (!parlors.length) return 1;
    return Math.max(...parlors.map(p => p.revenue), 1);
  });

  readonly lineChartOptions: ChartConfiguration<'line'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { maxTicksLimit: 10, font: { size: 11 } } },
      y: { grid: { color: '#f0f0f0' }, ticks: { font: { size: 11 } }, beginAtZero: true },
    },
    elements: { line: { tension: 0.4 }, point: { radius: 3, hoverRadius: 5 } },
  };

  readonly postsLineOptions: ChartConfiguration<'line'>['options'] = {
    ...this.lineChartOptions,
    elements: {
      line: { tension: 0.4 },
      point: { radius: 2, hoverRadius: 4 },
    },
  };

  readonly revenueChartOptions: ChartConfiguration<'line'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { maxTicksLimit: 10, font: { size: 11 } } },
      y: {
        grid: { color: '#f0f0f0' },
        ticks: {
          font: { size: 11 },
          callback: (value) => `₹${Number(value).toLocaleString('en-IN')}`,
        },
        beginAtZero: true,
      },
    },
    elements: { line: { tension: 0.4 }, point: { radius: 2, hoverRadius: 4 } },
  };

  readonly barChartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { maxTicksLimit: 10, font: { size: 11 } } },
      y: { grid: { color: '#f0f0f0' }, ticks: { font: { size: 11 } }, beginAtZero: true },
    },
  };

  readonly doughnutChartOptions: ChartConfiguration<'doughnut'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: { boxWidth: 12, padding: 12, font: { size: 11 } },
      },
    },
  };

  readonly userGrowthData = computed<ChartData<'line'>>(() => ({
    labels: this.analytics()?.user_growth?.map(d => d.date.slice(5)) ?? [],
    datasets: [
      {
        data: this.analytics()?.user_growth?.map(d => d.count) ?? [],
        label: 'New Users',
        fill: true,
        backgroundColor: 'rgba(115, 103, 240, 0.15)',
        borderColor: '#7367f0',
        borderWidth: 2,
        pointBackgroundColor: '#7367f0',
      },
    ],
  }));

  readonly revenueData = computed<ChartData<'line'>>(() => ({
    labels: this.analytics()?.revenue_per_day?.map(d => d.date.slice(5)) ?? [],
    datasets: [
      {
        data: this.analytics()?.revenue_per_day?.map(d => d.count) ?? [],
        label: 'Revenue',
        fill: true,
        backgroundColor: 'rgba(255, 159, 67, 0.15)',
        borderColor: '#ff9f43',
        borderWidth: 2,
        pointBackgroundColor: '#ff9f43',
      },
    ],
  }));

  readonly bookingsData = computed<ChartData<'bar'>>(() => ({
    labels: this.analytics()?.bookings_per_day?.map(d => d.date.slice(5)) ?? [],
    datasets: [
      {
        data: this.analytics()?.bookings_per_day?.map(d => d.count) ?? [],
        label: 'Bookings',
        backgroundColor: 'rgba(40, 199, 111, 0.85)',
        borderRadius: 6,
        maxBarThickness: 40,
      },
    ],
  }));

  readonly postsData = computed<ChartData<'line'>>(() => ({
    labels: this.analytics()?.posts_per_day?.map(d => d.date.slice(5)) ?? [],
    datasets: [
      {
        data: this.analytics()?.posts_per_day?.map(d => d.count) ?? [],
        label: 'Posts',
        fill: true,
        backgroundColor: 'rgba(0, 207, 232, 0.15)',
        borderColor: '#00cfe8',
        borderWidth: 2,
        pointBackgroundColor: '#00cfe8',
      },
    ],
  }));

  readonly gameDistributionData = computed<ChartData<'doughnut'>>(() => ({
    labels: this.analytics()?.game_distribution?.map(d => d.label) ?? [],
    datasets: [
      {
        data: this.analytics()?.game_distribution?.map(d => d.value) ?? [],
        backgroundColor: ['#7367f0', '#28c76f', '#ff9f43', '#ea5455', '#00cfe8', '#82868b'],
        borderWidth: 2,
        borderColor: '#fff',
      },
    ],
  }));

  ngOnInit(): void {
    this.loadAnalytics();
  }

  setPeriod(period: Period): void {
    if (this.activePeriod() === period) return;
    this.activePeriod.set(period);
    this.loadAnalytics();
  }

  formatNumber(value: number | null | undefined): string {
    if (value === null || value === undefined) return '0';
    return value.toLocaleString('en-IN');
  }

  formatPercent(value: number | null | undefined): string {
    if (value === null || value === undefined) return '0%';
    return `${value.toFixed(1)}%`;
  }

  bookingPercent(parlor: ParlorStat): number {
    return Math.round((parlor.bookings_count / this.maxBookings()) * 100);
  }

  revenuePercent(parlor: ParlorRevenueStat): number {
    return Math.round((parlor.revenue / this.maxRevenue()) * 100);
  }

  exportCsv(): void {
    const data = this.analytics();
    if (!data) return;

    const rows: string[][] = [
      ['Metric', 'Value'],
      ['Period', this.activePeriod()],
      ['Total Users', String(data.total_users)],
      ['New Users (period)', String(data.new_users)],
      ['Total Bookings', String(data.total_bookings)],
      ['Revenue', String(data.revenue)],
      ['Conversion Rate', String(data.conversion_rate)],
      ['Cancellation Rate', String(data.cancellation_rate)],
      [],
      ['Date', 'New Users'],
      ...data.user_growth.map(d => [d.date, String(d.count)]),
      [],
      ['Date', 'Bookings'],
      ...data.bookings_per_day.map(d => [d.date, String(d.count)]),
      [],
      ['Date', 'Revenue'],
      ...(data.revenue_per_day ?? []).map(d => [d.date, String(d.count)]),
      [],
      ['Date', 'Posts'],
      ...data.posts_per_day.map(d => [d.date, String(d.count)]),
      [],
      ['Parlor', 'Bookings'],
      ...data.top_parlors.map(p => [p.parlor_name, String(p.bookings_count)]),
      [],
      ['Parlor', 'Revenue'],
      ...(data.top_parlors_by_revenue ?? []).map(p => [p.parlor_name, String(p.revenue)]),
    ];

    const csv = rows.map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `analytics-${this.activePeriod()}-${new Date().toISOString().slice(0, 10)}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
    this.toast.success('Analytics exported');
  }

  loadAnalytics(): void {
    this.loadError.set(false);
    this.analytics.set(null);
    this.api
      .getAnalytics(this.activePeriod())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: data => this.analytics.set(data),
        error: () => {
          this.loadError.set(true);
          this.toast.error('Failed to load analytics');
        },
      });
  }
}