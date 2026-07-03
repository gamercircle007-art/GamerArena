/** Unified chart colors for Recharts across dashboard & analytics */
export const CHART = {
  primary: '#6366F1',
  primaryLight: '#818CF8',
  violet: '#8B5CF6',
  cyan: '#06B6D4',
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  pink: '#EC4899',
  grid: '#E2E8F0',
  axis: '#94A3B8',
  tooltip: {
    bg: '#1E293B',
    border: '#334155',
  },
} as const;

export const PIE_COLORS = [
  CHART.primary,
  CHART.violet,
  CHART.cyan,
  CHART.success,
  CHART.warning,
  CHART.danger,
  CHART.pink,
] as const;

export const chartAxisProps = {
  tick: { fontSize: 11, fill: CHART.axis },
  axisLine: { stroke: CHART.grid },
  tickLine: false,
} as const;

export const chartTooltipStyle = {
  backgroundColor: CHART.tooltip.bg,
  border: `1px solid ${CHART.tooltip.border}`,
  borderRadius: 8,
  fontSize: 12,
  color: '#F8FAFC',
} as const;