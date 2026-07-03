import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { formatDate } from '../../utils/formatters';
import { ChartCard, ChartSkeleton } from '../ui/ChartCard';
import { CHART, chartAxisProps, chartTooltipStyle } from '@/lib/chart-theme';

interface Props {
  title: string;
  subtitle?: string;
  data: { date: string; count: number }[];
  color?: string;
  loading?: boolean;
  height?: number;
}

export default function AreaChartCard({ title, subtitle, data, color = CHART.primary, loading, height = 220 }: Props) {
  const gradId = `grad-${title.replace(/\s/g, '')}`;
  return (
    <ChartCard title={title} subtitle={subtitle}>
      {loading ? (
        <ChartSkeleton height={height} />
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.2} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
            <XAxis dataKey="date" {...chartAxisProps} tickFormatter={d => d.slice(5)} />
            <YAxis {...chartAxisProps} width={32} />
            <Tooltip contentStyle={chartTooltipStyle} formatter={(v: number) => [v, 'Count']} labelFormatter={d => formatDate(d)} />
            <Area type="monotone" dataKey="count" stroke={color} strokeWidth={2} fill={`url(#${gradId})`} />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </ChartCard>
  );
}