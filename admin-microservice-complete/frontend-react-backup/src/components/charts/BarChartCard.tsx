import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
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

export default function BarChartCard({ title, subtitle, data, color = CHART.success, loading, height = 220 }: Props) {
  return (
    <ChartCard title={title} subtitle={subtitle}>
      {loading ? (
        <ChartSkeleton height={height} />
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART.grid} vertical={false} />
            <XAxis dataKey="date" {...chartAxisProps} tickFormatter={d => d.slice(5)} />
            <YAxis {...chartAxisProps} width={32} />
            <Tooltip contentStyle={chartTooltipStyle} formatter={(v: number) => [v, 'Count']} />
            <Bar dataKey="count" fill={color} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </ChartCard>
  );
}