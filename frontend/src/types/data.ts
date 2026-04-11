export type ChartMeta = {
  project: string
  tab: string
  snapshot_date: string
  academic_year?: string
  degree_level: string
  source: string
  source_url?: string | null
  methodology: string
  disclaimer?: string
  filter_fingerprint?: string
}

export type BarChartSpec = {
  type: 'bar'
  title: string
  data: { label: string; value: number }[]
}

export type MetricSpec = {
  type: 'metric'
  title: string
  value: number
  unit: string
}

export type TrendSeriesSpec = {
  dataKey: string
  label: string
  color?: string
}

export type TrendChartSpec = {
  type: 'trend'
  title: string
  x_key?: string
  data: Record<string, string | number | undefined>[]
  series: TrendSeriesSpec[]
}

export type ChartSpec = BarChartSpec | MetricSpec | TrendChartSpec

export type TabBundle = {
  meta: ChartMeta
  charts: Record<string, ChartSpec>
}

export type SiteMeta = {
  site: { name: string; tagline: string }
  github_repo?: string
  github_project: string
  methodology_blurb: string
  tabs: { id: string; label: string }[]
}

export const tabDataPath: Record<string, string> = {
  industry: '/data/industry.json',
  postgrad: '/data/postgrad.json',
  international: '/data/international.json',
  origins_undergrad: '/data/origins_undergrad.json',
  origins_graduate: '/data/origins_graduate.json',
  origins_doctorate: '/data/origins_doctorate.json',
}
