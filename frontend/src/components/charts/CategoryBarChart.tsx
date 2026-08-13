import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { CategoricalStatistics } from '../../types/analytics'

interface CategoryBarChartProps {
  column: string
  statistics: CategoricalStatistics | undefined
}

export function CategoryBarChart({ column, statistics }: CategoryBarChartProps) {
  if (!statistics || statistics.top_values.length === 0) {
    return <p className="inline-note">No categorical values available for {column}.</p>
  }

  return (
    <div className="chart-shell">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={statistics.top_values} margin={{ top: 8, right: 8, bottom: 16, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="value" tickLine={false} axisLine={false} interval={0} />
          <YAxis tickLine={false} axisLine={false} allowDecimals={false} />
          <Tooltip
            formatter={(value, name) => [name === 'count' ? value : value, name === 'count' ? 'Count' : name]}
            labelFormatter={(label) => `${column}: ${label}`}
          />
          <Bar dataKey="count" radius={[8, 8, 0, 0]} fill="var(--accent)">
            {statistics.top_values.map((entry, index) => (
              <Cell key={`${entry.value}-${index}`} fill={index === 0 ? 'var(--accent)' : 'rgba(14, 116, 144, 0.55)'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}