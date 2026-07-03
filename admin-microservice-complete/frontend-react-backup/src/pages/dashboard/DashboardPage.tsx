import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Users, Store, Trophy, Ticket, FileText, Calendar, Globe, Star, BadgeCheck } from 'lucide-react';
import { toast } from 'sonner';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend, CartesianGrid,
} from 'recharts';
import { PageShell, StatCard, ChartCard, ChartSkeleton, DataTable } from '@/components/ui';
import { Button } from '@/components/ui/button';
import { adminApi } from '@/api/admin.api';
import { formatDate, formatNumber } from '@/utils/formatters';
import { CHART, PIE_COLORS, chartAxisProps, chartTooltipStyle } from '@/lib/chart-theme';
import { topParlorsColumns, recentUsersColumns } from './dashboardColumns';

export default function DashboardPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [period, setPeriod] = useState<'7d' | '30d' | '90d'>('30d');

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: adminApi.getStats,
    refetchInterval: 60_000,
  });

  const { data: analytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ['admin-analytics', period],
    queryFn: () => adminApi.getAnalytics(period),
  });

  const { data: recentUsers, isLoading: usersLoading } = useQuery({
    queryKey: ['recent-users'],
    queryFn: () => adminApi.getUsers({ limit: 5, page: 1 }),
  });

  const { data: pendingParlors } = useQuery({
    queryKey: ['pending-parlors'],
    queryFn: () => adminApi.getParlors({ is_verified: false, limit: 5 }),
  });

  const verifyMutation = useMutation({
    mutationFn: (id: string) => adminApi.verifyParlor(id, true),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pending-parlors'] });
      qc.invalidateQueries({ queryKey: ['admin-stats'] });
      toast.success('Parlor verified');
    },
  });

  const kpiCards = stats ? [
    { title: 'Total Users', value: formatNumber(stats.total_users), Icon: Users, color: 'indigo' as const, trend: 12, subtitle: `+${stats.new_users_today} today` },
    { title: 'Total Parlors', value: formatNumber(stats.total_parlors), Icon: Store, color: 'violet' as const, subtitle: `${stats.pending_verification} pending` },
    { title: 'Active Tournaments', value: formatNumber(stats.active_tournaments), Icon: Trophy, color: 'amber' as const, trend: 5, subtitle: `${stats.total_tournaments} total` },
    { title: 'Total Bookings', value: formatNumber(stats.total_bookings), Icon: Ticket, color: 'green' as const, trend: 8, subtitle: `+${stats.new_bookings_today} today` },
    { title: 'Total Posts', value: formatNumber(stats.total_posts), Icon: FileText, color: 'cyan' as const, subtitle: 'Social feed' },
    { title: 'Total Events', value: formatNumber(stats.total_events), Icon: Calendar, color: 'pink' as const, subtitle: 'Parlor events' },
    { title: 'Community', value: formatNumber(stats.total_community_posts), Icon: Globe, color: 'violet' as const, subtitle: 'Forum posts' },
    { title: 'Ratings', value: formatNumber(stats.total_ratings), Icon: Star, color: 'amber' as const, subtitle: 'Reviews' },
  ] : [];

  const topParlors = useMemo(
    () => (analytics?.top_parlors ?? []).slice(0, 6),
    [analytics?.top_parlors],
  );

  return (
    <PageShell>
      {/* Page header */}
      <div className="gc-section-header">
        <div>
          <h1 className="gc-page-title">Dashboard</h1>
          <p className="gc-page-subtitle">Platform overview and key metrics</p>
        </div>
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
      </div>

      {/* KPI grid */}
      <section className="gc-section" aria-label="Key metrics">
        <div className="gc-stat-grid">
          {statsLoading
            ? Array.from({ length: 8 }).map((_, i) => <StatCard key={i} title="" value="" Icon={Users} loading />)
            : kpiCards.map(c => <StatCard key={c.title} {...c} />)
          }
        </div>
      </section>

      {/* Charts */}
      <section className="gc-section" aria-label="Analytics charts">
        <div className="gc-chart-grid">
          <ChartCard title="User Growth" subtitle="New signups per day">
            {analyticsLoading ? <ChartSkeleton /> : (
              <ResponsiveContainer width="100%" height={240}>
                <AreaChart data={analytics?.users_growth ?? []} margin={{ top: 4, right: 4, left: -8, bottom: 0 }}>
                  <defs>
                    <linearGradient id="ugGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={CHART.primary} stopOpacity={0.22} />
                      <stop offset="95%" stopColor={CHART.primary} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
                  <XAxis dataKey="date" {...chartAxisProps} tickFormatter={d => d.slice(5)} />
                  <YAxis {...chartAxisProps} width={36} />
                  <Tooltip contentStyle={chartTooltipStyle} formatter={(v: number) => [v, 'Users']} labelFormatter={d => formatDate(d)} />
                  <Area type="monotone" dataKey="count" stroke={CHART.primary} strokeWidth={2.5} fill="url(#ugGrad)" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </ChartCard>

          <ChartCard title="Daily Bookings" subtitle="Tournament + slot bookings">
            {analyticsLoading ? <ChartSkeleton /> : (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={analytics?.bookings_per_day ?? []} margin={{ top: 4, right: 4, left: -8, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
                  <XAxis dataKey="date" {...chartAxisProps} tickFormatter={d => d.slice(5)} />
                  <YAxis {...chartAxisProps} width={36} />
                  <Tooltip contentStyle={chartTooltipStyle} formatter={(v: number) => [v, 'Bookings']} />
                  <Bar dataKey="count" fill={CHART.success} radius={[6, 6, 0, 0]} maxBarSize={40} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </ChartCard>

          <ChartCard title="Game Type Distribution" subtitle="Games across all parlors">
            {analyticsLoading ? <ChartSkeleton /> : (
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={analytics?.game_type_distribution ?? [{ name: 'No data', value: 1 }]}
                    cx="50%" cy="45%" innerRadius={58} outerRadius={88}
                    dataKey="value" nameKey="name" paddingAngle={3}
                  >
                    {(analytics?.game_type_distribution ?? []).map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} stroke="white" strokeWidth={2} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={chartTooltipStyle} />
                  <Legend iconSize={8} iconType="circle" wrapperStyle={{ fontSize: 11, paddingTop: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </ChartCard>

        </div>

        <DataTable
          title="Top Parlors"
          subtitle={`Ranked by bookings — last ${period}`}
          columns={topParlorsColumns}
          data={topParlors}
          isLoading={analyticsLoading}
          emptyMessage="No booking data yet"
        />
      </section>

      {/* Data tables */}
      <section className="gc-section" aria-label="Recent activity">
        <div className="gc-chart-grid">
          <DataTable
            title="Recent Registrations"
            subtitle="Latest user signups"
            columns={recentUsersColumns}
            data={recentUsers?.items ?? []}
            isLoading={usersLoading}
            emptyMessage="No recent users"
            onRowClick={row => navigate(`/users/${row.id}`)}
          />

          <div className="gc-card-flat overflow-hidden">
            <div className="gc-card-header">
              <h3 className="gc-section-title">Pending Verifications</h3>
              <p className="gc-section-subtitle">Parlors awaiting approval</p>
            </div>
            <div className="divide-y divide-slate-100">
              {(pendingParlors?.items ?? []).map(p => (
                <div key={p.id} className="flex items-center justify-between gap-3 px-4 sm:px-5 py-3.5 hover:bg-indigo-50/30 transition-colors">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="size-9 rounded-lg bg-amber-50 flex items-center justify-center ring-1 ring-amber-100 shrink-0">
                      <Store size={15} className="text-amber-600" aria-hidden />
                    </div>
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-slate-800 truncate">{p.name}</div>
                      <div className="text-xs text-slate-400 truncate">{p.owner_name}</div>
                    </div>
                  </div>
                  <Button size="sm" className="gc-btn-primary shrink-0" onClick={() => verifyMutation.mutate(p.id)} disabled={verifyMutation.isPending}>
                    Verify
                  </Button>
                </div>
              ))}
              {!pendingParlors?.items?.length && (
                <p className="px-5 py-10 text-center text-sm text-slate-400">All parlors verified</p>
              )}
            </div>
          </div>
        </div>
      </section>

      {(stats?.pending_verification ?? 0) > 0 && (
        <div className="gc-alert-info">
          <BadgeCheck size={18} className="text-amber-600 shrink-0" aria-hidden />
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-amber-900">
              {stats?.pending_verification} parlor{stats!.pending_verification > 1 ? 's' : ''} awaiting verification
            </p>
            <p className="text-xs text-amber-700 mt-0.5">Review accounts to grant the verified badge.</p>
          </div>
          <a href="/parlors?filter=unverified" className="gc-btn gc-btn-sm gc-btn-secondary whitespace-nowrap">
            Review →
          </a>
        </div>
      )}
    </PageShell>
  );
}