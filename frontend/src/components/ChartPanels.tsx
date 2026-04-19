import { ResponsiveSankey } from '@nivo/sankey'
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
  SankeyChartSpec,
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

function BarPanel({
  spec,
  valueLabel = 'Count',
}: {
  spec: BarChartSpec
  valueLabel?: string
}) {
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
                valueLabel,
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

function SankeyPanel({ spec }: { spec: SankeyChartSpec }) {
  const data = {
    nodes: spec.nodes.map((n) => ({
      id: n.id,
      label: n.label,
    })),
    links: spec.links.map((l) => ({
      source: l.source,
      target: l.target,
      value: l.value,
    })),
  }

  return (
    <div className="sankey-panel">
      <h3 className="chart-title">{spec.title}</h3>
      <div className="chart-wrap chart-wrap--sankey">
        <ResponsiveSankey
          data={data}
          margin={{ top: 12, right: 140, bottom: 12, left: 50 }}
          align="justify"
          sort="input"
          colors={{ scheme: 'set2' }}
          nodeOpacity={1}
          nodeHoverOpacity={1}
          nodeThickness={16}
          nodeSpacing={20}
          nodeBorderWidth={0}
          linkOpacity={0.45}
          linkHoverOpacity={0.65}
          linkContract={3}
          enableLinkGradient
          labelPosition="outside"
          labelOrientation="horizontal"
          labelPadding={12}
          legends={[
            {
              anchor: 'bottom-right',
              direction: 'column',
              translateX: 130,
              itemWidth: 100,
              itemHeight: 14,
              symbolShape: 'circle',
            },
          ]}
          theme={{
            labels: {
              text: {
                fontSize: 11,
              },
            },
            tooltip: {
              container: {
                fontSize: 12,
              },
            },
          }}
        />
      </div>
      <p className="muted small sankey-note">
        Each flow shows how many people in this <strong>demo dataset</strong>{' '}
        moved from one job stage to the next. Wider bands mean more people;
        this is not a map of one person’s résumé. Real data would come from
        surveys or employer rollups you trust.
      </p>
    </div>
  )
}

export function renderChart(key: string, spec: ChartSpec) {
  if (spec.type === 'metric') {
    return <MetricPanel key={key} spec={spec} />
  }
  if (spec.type === 'bar') {
    const isEmployers = key === 'top_employers'
    const isIntlProxy =
      key === 'aggregate_destination_proxy' ||
      key === 'post_graduation_destination_country' ||
      key === 'destination_country'
    const isRankBar = key.includes('rank')
    return (
      <BarPanel
        key={key}
        spec={spec}
        valueLabel={
          isRankBar
            ? 'Rank (lower is better)'
            : isEmployers || isIntlProxy
              ? 'Estimated count'
              : 'Count'
        }
      />
    )
  }
  if (spec.type === 'trend') {
    return <TrendPanel key={key} spec={spec} />
  }
  if (spec.type === 'sankey') {
    return <SankeyPanel key={key} spec={spec} />
  }
  return null
}
