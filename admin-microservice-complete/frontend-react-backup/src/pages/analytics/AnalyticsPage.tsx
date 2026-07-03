import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Download, Users, UserPlus, Ticket, IndianRupee } from 'lucide-react';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid,
} from 'recharts';
import {
  PageShell, Button, StatCard, ErrorBanner, ChartCard, ChartSkeleton, DataTable,
} from '@/components/ui';
import { topParlorsColumns } from '../dashboard/dashboardColumns';
import { adminApi } from '../../api/admin.api';
import { formatDate, formatCurrency, formatNumber } from '../../utils/formatters';
import { CHART, PIE_COLORS, chartAxisProps, chartTooltipStyle } from '@/lib/chart-theme';
import type { AnalyticsData } from '../../types';

export default function AnalyticsPage() {
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d');

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: adminApi.getStats,
  });

  const { data: analytics, isLoading: analyticsLoading, isError, refetch } = useQuery({
    queryKey: ['admin-analytics', period],
    queryFn: () => adminApi.getAnalytics(period),
  });

  const newThisPeriod = (analytics?.users_growth ?? []).reduce((s, d) => s + d.count, 0);
  const revenuePeriod = (analytics?.top_parlors ?? []).reduce((s, p) => s + p.revenue, 0);

  const topParlors = useMemo(
    () => (analytics?.top_parlors ?? []).slice(0, 10),
    [analytics?.top_parlors],
  );

  const exportCsv = () => {
    if (!analytics) return;
    const rows = [
      ['Metric', 'Value'],
      ['Period', period],
      ['Total Users', String(stats?.total_users ?? 0)],
      ['New Users (period)', String(newThisPeriod)],
      ['Total Bookings', String(stats?.total_bookings ?? 0)],
      ['Revenue (period)', String(revenuePeriod)],
      [],
      ['Date', 'New Users'],
      ...(analytics.users_growth.map(d => [d.date, String(d.count)])),
      [],
      ['Date', 'Bookings'],
      ...(analytics.bookings_per_day.map(d => [d.date, String(d.count)])),
      [],
      ['Parlor', 'Bookings', 'Revenue'],
      ...(analytics.top_parlors.map(p => [p.parlor_name, String(p.bookings_count), String(p.revenue)])),
    ];
    const csv = rows.map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics-${period}-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <PageShell>
      <div className="gc-section-header">
        <div>
          <h1 className="gc-page-title">Analytics</h1>
          <p className="gc-page-subtitle">Platform growth and revenue insights</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <div className="gc-period-picker" role="group" aria-label="Analytics period">
            {(['7d', '30d', '90d'] as const).map(p => (
              <button
                key={p}
                type="button"
                onClick={() => setPeriod(p)}
                className={period === p ? 'gc-period-btn-active' : 'gc-period-btn'}
                aria-pressed={period === p}
              >
                {p}
              </button>
            ))}
          </div>
          <Button variant="secondary" onClick={exportCsv} disabled={!analytics}>
            <Download size={14} /> Export CSV
          </Button>
        </div>
      </div>

      {isError && (
        <div className="gc-card overflow-hidden">
          <ErrorBanner message="Failed to load analytics" onRetry={() => refetch()} />
        </div>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        <StatCard title="Total Users" value={statsLoading ? '' : formatNumber(stats?.total_users ?? 0)} Icon={Users} color="indigo" loading={statsLoading} />
        <StatCard title="New This Period" value={analyticsLoading ? '' : formatNumber(newThisPeriod)} Icon={UserPlus} color="green" loading={analyticsLoading} subtitle={period} />
        <StatCard title="Total Bookings" value={statsLoading ? '' : formatNumber(stats?.total_bookings ?? 0)} Icon={Ticket} color="green" loading={statsLoading} />
        <StatCard title="Revenue This Period" value={analyticsLoading ? '' : formatCurrency(revenuePeriod)} Icon={IndianRupee} color="amber" loading={analyticsLoading} subtitle={period} />
      </div>

      <ChartCard title="User Growth" subtitle="New signups per day">
        {analyticsLoading ? <ChartSkeleton height={260} /> : (
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={analytics?.users_growth ?? []} margin={{ top: 4, right: 4, left: -8, bottom: 0 }}>
              <defs>
                <linearGradient id="anUgGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={CHART.primary} stopOpacity={0.22} />
                  <stop offset="95%" stopColor={CHART.primary} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
              <XAxis dataKey="date" {...chartAxisProps} tickFormatter={d => d.slice(5)} />
              <YAxis {...chartAxisProps} width={36} />
              <Tooltip contentStyle={chartTooltipStyle} formatter={(v: number) => [v, 'Users']} labelFormatter={d => formatDate(d)} />
              <Area type="monotone" dataKey="count" stroke={CHART.primary} strokeWidth={2} fill="url(#anUgGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      <ChartCard title="Bookings per Day" subtitle="Tournament + slot bookings">
        {analyticsLoading ? <ChartSkeleton height={260} /> : (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={analytics?.bookings_per_day ?? []} margin={{ top: 4, right: 4, left: -8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
              <XAxis dataKey="date" {...chartAxisProps} tickFormatter={d => d.slice(5)} />
              <YAxis {...chartAxisProps} width={36} />
              <Tooltip contentStyle={chartTooltipStyle} formatter={(v: number) => [v, 'Bookings']} />
              <Bar dataKey="count" fill={CHART.success} radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </ChartCard>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        <ChartCard title="Posts per Day" subtitle="Social feed activity">
          {analyticsLoading ? <ChartSkeleton height={220} /> : (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={analytics?.posts_per_day ?? []} margin={{ top: 4, right: 4, left: -8, bottom: 0 }}>
                <defs>
                  <linearGradient id="anPgGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={CHART.cyan} stopOpacity={0.22} />
                    <stop offset="95%" stopColor={CHART.cyan} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
                <XAxis dataKey="date" {...chartAxisProps} tickFormatter={d => d.slice(5)} />
                <YAxis {...chartAxisProps} width={28} />
                <Tooltip contentStyle={chartTooltipStyle} formatter={(v: number) => [v, 'Posts']} />
                <Area type="monotone" dataKey="count" stroke={CHART.cyan} strokeWidth={2} fill="url(#anPgGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Game Distribution" subtitle="Games across all parlors">
          {analyticsLoading ? <ChartSkeleton height={220} /> : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={analytics?.game_type_distribution ?? [{ name: 'No data', value: 1 }]}
                  cx="50%" cy="50%" innerRadius={50} outerRadius={80}
                  dataKey="value" nameKey="name"
                >
                  {(analytics?.game_type_distribution ?? []).map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={chartTooltipStyle} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      <ChartCard title="Top Parlors" subtitle="By total bookings">
        {analyticsLoading ? <ChartSkeleton height={220} /> : (
          <TopParlorsChart data={analytics?.top_parlors ?? []} />
        )}
      </ChartCard>

      <DataTable
        title="Top Parlors"
        subtitle="Ranked by bookings and revenue"
        columns={topParlorsColumns}
        data={topParlors}
        isLoading={analyticsLoading}
        emptyMessage="No parlor data yet"
      />
    </PageShell>
  );
}

function TopParlorsChart({ data }: { data: AnalyticsData['top_parlors'] }) {
  const top = data.slice(0, 10);
  const chartData = [...top].reverse().map(p => ({
    name: p.parlor_name.length > 18 ? `${p.parlor_name.slice(0, 18)}…` : p.parlor_name,
    bookings: p.bookings_count,
  }));

  if (!top.length) {
    return <p className="gc-empty-text py-12">No parlor data yet</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, top.length * 28)}>
      <BarChart data={chartData} layout="vertical" margin={{ left: 8, right: 16 }}>
        <XAxis type="number" {...chartAxisProps} />
        <YAxis type="category" dataKey="name" {...chartAxisProps} width={120} />
        <Tooltip contentStyle={chartTooltipStyle} formatter={(v: number) => [v, 'Bookings']} />
        <Bar dataKey="bookings" fill={CHART.primary} radius={[0, 3, 3, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}