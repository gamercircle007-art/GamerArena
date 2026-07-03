import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { ChartCard, ChartSkeleton } from '../ui/ChartCard';

const DEFAULT_COLORS = ['#6366F1', '#8B5CF6', '#06B6D4', '#10B981', '#F59E0B', '#EF4444', '#EC4899'];

interface Props {
  title: string;
  subtitle?: string;
  data: { name: string; value: number; color?: string }[];
  loading?: boolean;
  height?: number;
}

export default function PieChartCard({ title, subtitle, data, loading, height = 220 }: Props) {
  const total = data.reduce((s, d) => s + d.value, 0);
  return (
    <ChartCard title={title} subtitle={subtitle}>
      {loading ? (
        <ChartSkeleton height={height} />
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          <PieChart>
            <Pie data={data.length ? data : [{ name: 'No data', value: 1 }]} cx="50%" cy="50%"
              innerRadius={55} outerRadius={85} dataKey="value" nameKey="name">
              {data.map((d, i) => (
                <Cell key={i} fill={d.color ?? DEFAULT_COLORS[i % DEFAULT_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend iconSize={10} wrapperStyle={{ fontSize: 12 }} />
            <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" className="text-sm font-bold fill-slate-700">
              {total}
            </text>
          </PieChart>
        </ResponsiveContainer>
      )}
    </ChartCard>
  );
}