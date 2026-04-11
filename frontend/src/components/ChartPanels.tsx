import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type {
  BarChartSpec,
  ChartSpec,
  MetricSpec,
  TrendChartSpec,
} from '../types/data'

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

function TrendPanel({ spec }: { spec: TrendChartSpec }) {
  const xKey = spec.x_key ?? 'year'
  return (
    <div className="trend-panel">
      <h3 className="chart-title">{spec.title}</h3>
      <div className="chart-wrap chart-wrap--trend">
        <ResponsiveContainer width="100%" height={340}>
          <LineChart
            data={spec.data}
            margin={{ top: 8, right: 16, left: 4, bottom: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" opacity={0.35} />
            <XAxis
              dataKey={xKey}
              tick={{ fontSize: 12 }}
              tickFormatter={(v) => String(v)}
            />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip
              formatter={(v) =>
                typeof v === 'number' ? v.toLocaleString() : String(v)
              }
            />
            <Legend />
            {spec.series.map((s) => (
              <Line
                key={s.dataKey}
                type="monotone"
                dataKey={s.dataKey}
                name={s.label}
                stroke={s.color ?? barColor}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <p className="trend-note muted small">
        Series labels describe synthetic 1y / 5y / 10y-style windows for
        development; replace with real cohort definitions in production data.
      </p>
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
  if (spec.type === 'trend') {
    return <TrendPanel key={key} spec={spec} />
  }
  return null
}
