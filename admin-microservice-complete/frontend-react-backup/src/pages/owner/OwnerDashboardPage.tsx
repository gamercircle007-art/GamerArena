import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Ticket, IndianRupee, Users, Star, Plus, Calendar, FileText, Tag } from 'lucide-react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import {
  PageShell, PageHeader, StatCard, ChartCard, ChartSkeleton, Button, DataTable,
} from '../../components/ui';
import { getOwnerBookingColumns, getOwnerEventColumns } from '../_shared/listColumns';
import { adminApi } from '../../api/admin.api';
import { formatCurrency } from '../../utils/formatters';
import { CHART, chartAxisProps, chartTooltipStyle } from '@/lib/chart-theme';
import { useAuthStore } from '../../context/AuthContext';

const QUICK_ACTIONS = [
  { label: 'New Slot', Icon: Plus, color: 'bg-emerald-600' },
  { label: 'New Event', Icon: Calendar, color: 'bg-indigo-600' },
  { label: 'New Offer', Icon: Tag, color: 'bg-amber-600' },
  { label: 'New Post', Icon: FileText, color: 'bg-violet-600' },
] as const;

export default function OwnerDashboardPage() {
  const user = useAuthStore(s => s.user);

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['owner-stats'],
    queryFn: adminApi.getOwnerStats,
  });

  const { data: bookings, isLoading: bookingsLoading } = useQuery({
    queryKey: ['owner-bookings'],
    queryFn: () => adminApi.getBookings({ limit: 5, parlor_owner: true }),
  });

  const { data: events, isLoading: eventsLoading } = useQuery({
    queryKey: ['owner-events'],
    queryFn: () => adminApi.getEvents({ limit: 5, upcoming: true }),
  });

  const bookingColumns = useMemo(() => getOwnerBookingColumns(), []);
  const eventColumns = useMemo(() => getOwnerEventColumns(), []);

  return (
    <PageShell>
      <PageHeader
        title={`Welcome back, ${user?.name ?? 'Owner'}`}
        subtitle={user?.parlor_name ?? 'Your parlor dashboard'}
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <StatCard title="Today's Bookings" value={statsLoading ? '' : String(stats?.today_bookings ?? 0)} Icon={Ticket} color="green" loading={statsLoading} />
        <StatCard title="This Week Revenue" value={statsLoading ? '' : formatCurrency(stats?.week_revenue ?? 0)} Icon={IndianRupee} color="amber" loading={statsLoading} />
        <StatCard title="Followers" value={statsLoading ? '' : String(stats?.followers ?? 0)} Icon={Users} color="indigo" loading={statsLoading} />
        <StatCard title="Avg Rating" value={statsLoading ? '' : (stats?.avg_rating ?? 0).toFixed(1)} Icon={Star} color="violet" loading={statsLoading} />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {QUICK_ACTIONS.map(a => (
          <Button key={a.label} className={`${a.color} text-white border-0 hover:opacity-90`}>
            <a.Icon size={16} /> {a.label}
          </Button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        <ChartCard title="Bookings Trend (7 days)">
          {statsLoading ? <ChartSkeleton height={180} /> : (
            <ResponsiveContainer width="100%" height={180}>
              <AreaChart data={stats?.bookings_trend ?? []} margin={{ top: 4, right: 4, left: -8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
                <XAxis dataKey="date" {...chartAxisProps} tickFormatter={d => d.slice(5)} />
                <YAxis {...chartAxisProps} width={28} />
                <Tooltip contentStyle={chartTooltipStyle} />
                <Area type="monotone" dataKey="count" stroke={CHART.primary} fill={CHART.primary} fillOpacity={0.1} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
        <ChartCard title="Revenue per Week">
          {statsLoading ? <ChartSkeleton height={180} /> : (
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={stats?.revenue_per_week ?? []} margin={{ top: 4, right: 4, left: -8, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
                <XAxis dataKey="week" {...chartAxisProps} />
                <YAxis {...chartAxisProps} width={40} />
                <Tooltip contentStyle={chartTooltipStyle} formatter={(v: number) => [formatCurrency(v), 'Revenue']} />
                <Bar dataKey="revenue" fill={CHART.success} radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        <DataTable
          title="Recent Bookings"
          columns={bookingColumns}
          data={bookings?.items ?? []}
          isLoading={bookingsLoading}
          emptyMessage="No recent bookings"
        />
        <DataTable
          title="Upcoming Events"
          columns={eventColumns}
          data={events?.items ?? []}
          isLoading={eventsLoading}
          emptyMessage="No upcoming events"
        />
      </div>
    </PageShell>
  );
}