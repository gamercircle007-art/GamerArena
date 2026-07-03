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
import { RouterLink } from '@angular/router';
import { NgIcon, provideIcons } from '@ng-icons/core';
import {
  bootstrapCalendarCheck,
  bootstrapClockHistory,
  bootstrapCurrencyRupee,
  bootstrapExclamationTriangle,
  bootstrapFileText,
  bootstrapPeople,
  bootstrapPersonPlus,
  bootstrapShop,
  bootstrapTrophy,
} from '@ng-icons/bootstrap-icons';
import { ChartConfiguration, ChartData } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';
import { ColumnMode, NgxDatatableModule } from '@swimlane/ngx-datatable';

import { AdminApiService } from '../../core/services/admin-api.service';
import { ToastService } from '../../core/services/toast.service';
import { AdminStats, AnalyticsData, Parlor, User } from '../../core/models';
import { PageHeaderComponent } from '../../shared/components/page-header/page-header.component';
import { StatsCardComponent } from '../../shared/components/stats-card/stats-card.component';
import { StatusBadgeComponent } from '../../shared/components/status-badge/status-badge.component';
import { CurrencyInPipe } from '../../shared/pipes/currency-in.pipe';
import { DateFormatPipe } from '../../shared/pipes/date-format.pipe';
import { ConfirmService } from '../../shared/services/confirm.service';

type Period = '7d' | '30d' | '90d';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    RouterLink,
    BaseChartDirective,
    NgxDatatableModule,
    NgIcon,
    PageHeaderComponent,
    StatsCardComponent,
    StatusBadgeComponent,
    DateFormatPipe,
    CurrencyInPipe,
  ],
  providers: [
    provideIcons({
      bootstrapPeople,
      bootstrapShop,
      bootstrapTrophy,
      bootstrapCalendarCheck,
      bootstrapPersonPlus,
      bootstrapClockHistory,
      bootstrapFileText,
      bootstrapCurrencyRupee,
      bootstrapExclamationTriangle,
    }),
  ],
  template: `
    <div class="dashboard-page">
      <app-page-header
        title="Dashboard"
        subtitle="Platform overview and key metrics"
        [breadcrumbs]="[{ label: 'Home', route: '/dashboard' }, { label: 'Dashboard' }]">
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
      </app-page-header>

      <!-- KPI Row 1 -->
      <div class="row g-3 g-xl-4 mb-3 mb-xl-4">
        <div class="col-6 col-xl-3">
          <app-stats-card
            title="Total Users"
            [value]="formatNumber(stats()?.users)"
            icon="bootstrapPeople"
            color="primary"
            [trend]="12"
            [subtitle]="'+' + (stats()?.new_users_today ?? 0) + ' today'" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card
            title="Total Parlors"
            [value]="formatNumber(stats()?.parlors)"
            icon="bootstrapShop"
            color="success"
            [subtitle]="(stats()?.pending_verification ?? 0) + ' pending'" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card
            title="Active Tournaments"
            [value]="formatNumber(stats()?.tournaments)"
            icon="bootstrapTrophy"
            color="warning"
            [trend]="5" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card
            title="Today's Bookings"
            [value]="formatNumber(stats()?.bookings)"
            icon="bootstrapCalendarCheck"
            color="danger"
            [trend]="8" />
        </div>
      </div>

      <!-- KPI Row 2 -->
      <div class="row g-3 g-xl-4 mb-4">
        <div class="col-6 col-xl-3">
          <app-stats-card
            title="New Users Today"
            [value]="formatNumber(stats()?.new_users_today)"
            icon="bootstrapPersonPlus"
            color="info" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card
            title="Pending Verification"
            [value]="formatNumber(stats()?.pending_verification)"
            icon="bootstrapClockHistory"
            color="warning" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card
            title="Total Posts"
            [value]="formatNumber(stats()?.posts)"
            icon="bootstrapFileText"
            color="primary" />
        </div>
        <div class="col-6 col-xl-3">
          <app-stats-card
            title="Total Revenue"
            [value]="stats()?.revenue | currencyIn"
            icon="bootstrapCurrencyRupee"
            color="success" />
        </div>
      </div>

      <!-- Charts Row 1 -->
      <div class="row g-3 g-xl-4 mb-3 mb-xl-4">
        <div class="col-xl-6">
          <div class="card chart-card h-100">
            <div class="card-header border-0 bg-white">
              <h6 class="mb-0 fw-bold">User Growth</h6>
              <small class="text-muted">Daily new signups — last {{ periodLabels[activePeriod()] }}</small>
            </div>
            <div class="card-body">
              @if (analytics()) {
                <div class="chart-container">
                  <canvas
                    baseChart
                    [data]="userGrowthData()"
                    [options]="lineChartOptions"
                    type="line">
                  </canvas>
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
              <h6 class="mb-0 fw-bold">Daily Bookings</h6>
              <small class="text-muted">Tournament + slot bookings</small>
            </div>
            <div class="card-body">
              @if (analytics()) {
                <div class="chart-container">
                  <canvas
                    baseChart
                    [data]="bookingsData()"
                    [options]="barChartOptions"
                    type="bar">
                  </canvas>
                </div>
              } @else {
                <div class="chart-skeleton"></div>
              }
            </div>
          </div>
        </div>
      </div>

      <!-- Charts Row 2 -->
      <div class="row g-3 g-xl-4 mb-4">
        <div class="col-xl-6">
          <div class="card chart-card h-100">
            <div class="card-header border-0 bg-white">
              <h6 class="mb-0 fw-bold">Game Type Distribution</h6>
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
        <div class="col-xl-6">
          <div class="card chart-card h-100">
            <div class="card-header border-0 bg-white">
              <h6 class="mb-0 fw-bold">Top Parlors by Bookings</h6>
              <small class="text-muted">Ranked by bookings — last {{ periodLabels[activePeriod()] }}</small>
            </div>
            <div class="card-body">
              @if (analytics()) {
                <div class="chart-container chart-container--horizontal">
                  <canvas
                    baseChart
                    [data]="topParlorsData()"
                    [options]="horizontalBarOptions"
                    type="bar">
                  </canvas>
                </div>
              } @else {
                <div class="chart-skeleton"></div>
              }
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Activity Tables -->
      <div class="row g-3 g-xl-4 mb-4">
        <div class="col-xl-6">
          <div class="card table-card h-100">
            <div class="card-header border-0 bg-white">
              <h6 class="mb-0 fw-bold">Recent Registrations</h6>
              <small class="text-muted">Latest user signups</small>
            </div>
            <div class="card-body p-0">
              <ngx-datatable
                class="bootstrap dashboard-table"
                [rows]="recentUsers()"
                [columnMode]="ColumnMode.force"
                [headerHeight]="48"
                [rowHeight]="56"
                [footerHeight]="0"
                [scrollbarH]="true"
                [limit]="5">
                <ngx-datatable-column name="User" [flexGrow]="2">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    <div class="fw-medium text-dark">{{ row.name || row.username || '—' }}</div>
                    <small class="text-muted">{{ row.email || row.phone_number || '—' }}</small>
                  </ng-template>
                </ngx-datatable-column>
                <ngx-datatable-column name="Role" [flexGrow]="1">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    <app-status-badge [status]="row.role" />
                  </ng-template>
                </ngx-datatable-column>
                <ngx-datatable-column name="Joined" [flexGrow]="1">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    {{ row.created_at | dateFormat }}
                  </ng-template>
                </ngx-datatable-column>
              </ngx-datatable>
              @if (!loadingUsers() && !recentUsers().length) {
                <div class="empty-state">No recent users</div>
              }
            </div>
          </div>
        </div>

        <div class="col-xl-6">
          <div class="card table-card h-100">
            <div class="card-header border-0 bg-white d-flex justify-content-between align-items-start">
              <div>
                <h6 class="mb-0 fw-bold">Pending Verification Queue</h6>
                <small class="text-muted">Parlors awaiting approval</small>
              </div>
            </div>
            <div class="card-body p-0">
              <ngx-datatable
                class="bootstrap dashboard-table"
                [rows]="pendingParlors()"
                [columnMode]="ColumnMode.force"
                [headerHeight]="48"
                [rowHeight]="56"
                [footerHeight]="0"
                [scrollbarH]="true"
                [limit]="5">
                <ngx-datatable-column name="Parlor" [flexGrow]="2">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    <div class="fw-medium text-dark">{{ row.name }}</div>
                    <small class="text-muted text-truncate d-block">{{ row.address || '—' }}</small>
                  </ng-template>
                </ngx-datatable-column>
                <ngx-datatable-column name="Status" [flexGrow]="1">
                  <ng-template ngx-datatable-cell-template>
                    <app-status-badge status="pending" />
                  </ng-template>
                </ngx-datatable-column>
                <ngx-datatable-column name="Actions" [flexGrow]="1" [sortable]="false">
                  <ng-template let-row="row" ngx-datatable-cell-template>
                    <button
                      type="button"
                      class="btn btn-sm btn-primary"
                      [disabled]="verifyingId() === row.id"
                      (click)="verifyParlor(row)">
                      @if (verifyingId() === row.id) {
                        <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                      } @else {
                        Verify
                      }
                    </button>
                  </ng-template>
                </ngx-datatable-column>
              </ngx-datatable>
              @if (!loadingParlors() && !pendingParlors().length) {
                <div class="empty-state">All parlors verified</div>
              }
            </div>
          </div>
        </div>
      </div>

      <!-- Amber Alert -->
      @if ((stats()?.pending_verification ?? 0) > 0) {
        <div class="alert alert-warning d-flex align-items-center gap-3 mb-0 dashboard-alert" role="alert">
          <ng-icon name="bootstrapExclamationTriangle" size="22" class="flex-shrink-0" />
          <div class="flex-grow-1">
            <strong>
              {{ stats()!.pending_verification }}
              parlor{{ stats()!.pending_verification! > 1 ? 's' : '' }} awaiting verification
            </strong>
            <p class="mb-0 small mt-1">Review accounts to grant the verified badge.</p>
          </div>
          <a routerLink="/parlors" [queryParams]="{ filter: 'unverified' }" class="btn btn-sm btn-warning flex-shrink-0">
            Review →
          </a>
        </div>
      }
    </div>
  `,
  styles: `
    .dashboard-page { padding-bottom: 0.5rem; }

    .period-selector .btn {
      min-width: 72px;
      font-size: 0.8125rem;
      font-weight: 600;
    }

    .chart-card .card-header,
    .table-card .card-header {
      padding: 1.25rem 1.5rem 0.5rem;
    }

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

    .chart-container--horizontal {
      height: 280px;
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

    .dashboard-table {
      box-shadow: none;
    }

    .empty-state {
      padding: 2.5rem 1rem;
      text-align: center;
      color: #b9b9c3;
      font-size: 0.875rem;
    }

    .dashboard-alert {
      border: 1px solid rgba(255, 159, 67, 0.35);
      background: rgba(255, 159, 67, 0.12);
      color: #7a4f12;
    }

    @keyframes shimmer {
      0% { background-position: 200% 0; }
      100% { background-position: -200% 0; }
    }
  `,
})
export class DashboardComponent implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly toast = inject(ToastService);
  private readonly confirm = inject(ConfirmService);
  private readonly destroyRef = inject(DestroyRef);

  readonly stats = signal<AdminStats | null>(null);
  readonly analytics = signal<AnalyticsData | null>(null);
  readonly recentUsers = signal<User[]>([]);
  readonly pendingParlors = signal<Parlor[]>([]);
  readonly activePeriod = signal<Period>('30d');
  readonly loadingUsers = signal(true);
  readonly loadingParlors = signal(true);
  readonly verifyingId = signal<string | null>(null);

  readonly periods: Period[] = ['7d', '30d', '90d'];
  readonly periodLabels: Record<Period, string> = {
    '7d': '7 Days',
    '30d': '30 Days',
    '90d': '90 Days',
  };

  protected readonly ColumnMode = ColumnMode;

  readonly lineChartOptions: ChartConfiguration<'line'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { maxTicksLimit: 8, font: { size: 11 } } },
      y: { grid: { color: '#f0f0f0' }, ticks: { font: { size: 11 } }, beginAtZero: true },
    },
    elements: { line: { tension: 0.4 }, point: { radius: 3, hoverRadius: 5 } },
  };

  readonly barChartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { maxTicksLimit: 8, font: { size: 11 } } },
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

  readonly horizontalBarOptions: ChartConfiguration<'bar'>['options'] = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { color: '#f0f0f0' }, ticks: { font: { size: 11 } }, beginAtZero: true },
      y: { grid: { display: false }, ticks: { font: { size: 11 } } },
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

  readonly topParlorsData = computed<ChartData<'bar'>>(() => {
    const parlors = this.analytics()?.top_parlors?.slice(0, 6) ?? [];
    return {
      labels: parlors.map(p => p.parlor_name),
      datasets: [
        {
          data: parlors.map(p => p.bookings_count),
          label: 'Bookings',
          backgroundColor: 'rgba(115, 103, 240, 0.85)',
          borderRadius: 4,
          maxBarThickness: 28,
        },
      ],
    };
  });

  ngOnInit(): void {
    this.loadStats();
    this.loadAnalytics();
    this.loadRecentUsers();
    this.loadPendingParlors();
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

  async verifyParlor(parlor: Parlor): Promise<void> {
    const confirmed = await this.confirm.confirm(
      'Verify Parlor',
      `Approve "${parlor.name}" and grant the verified badge?`,
      'Verify',
      'question',
    );
    if (!confirmed) return;

    this.verifyingId.set(parlor.id);
    this.api
      .verifyParlor(parlor.id, true)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.verifyingId.set(null);
          this.toast.success(`"${parlor.name}" has been verified`);
          this.loadStats();
          this.loadPendingParlors();
        },
        error: () => {
          this.verifyingId.set(null);
          this.toast.error('Failed to verify parlor. Please try again.');
        },
      });
  }

  private loadStats(): void {
    this.api
      .getStats()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(data => this.stats.set(data));
  }

  private loadAnalytics(): void {
    this.analytics.set(null);
    this.api
      .getAnalytics(this.activePeriod())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(data => this.analytics.set(data));
  }

  private loadRecentUsers(): void {
    this.loadingUsers.set(true);
    this.api
      .getUsers({ page: 1, limit: 5 })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.recentUsers.set(res.items);
          this.loadingUsers.set(false);
        },
        error: () => this.loadingUsers.set(false),
      });
  }

  private loadPendingParlors(): void {
    this.loadingParlors.set(true);
    this.api
      .getParlors({ is_verified: false, page: 1, limit: 5 })
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: res => {
          this.pendingParlors.set(res.items);
          this.loadingParlors.set(false);
        },
        error: () => this.loadingParlors.set(false),
      });
  }
}