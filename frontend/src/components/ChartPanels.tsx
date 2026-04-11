import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { BarChartSpec, ChartSpec, MetricSpec } from '../types/data'

const barColor = '#c5050c'

function MetricPanel({ spec }: { spec: MetricSpec }) {
  const suffix = spec.unit === 'percent' ? '%' : ` ${spec.unit}`
  return (
    <div className="metric-panel">
      <h3 className="chart-title">{spec.title}</h3>
      <p className="metric-value">
        {spec.value}
        {suffix}
      </p>
    </div>
  )
}

function BarPanel({ spec }: { spec: BarChartSpec }) {
  const rows = spec.data.map((d) => ({ name: d.label, value: d.value }))
  return (
    <div className="bar-panel">
      <h3 className="chart-title">{spec.title}</h3>
      <div className="chart-wrap">
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            data={rows}
            margin={{ top: 8, right: 12, left: 4, bottom: 72 }}
          >
            <XAxis
              dataKey="name"
              angle={-32}
              textAnchor="end"
              height={88}
              interval={0}
              tick={{ fontSize: 12 }}
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              cursor={{ fill: 'rgba(197, 5, 12, 0.08)' }}
              formatter={(v) => [
                typeof v === 'number' ? v.toLocaleString() : String(v),
                'Count',
              ]}
            />
            <Bar dataKey="value" fill={barColor} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export function renderChart(key: string, spec: ChartSpec) {
  if (spec.type === 'metric') {
    return <MetricPanel key={key} spec={spec} />
  }
  if (spec.type === 'bar') {
    return <BarPanel key={key} spec={spec} />
  }
  return null
}
