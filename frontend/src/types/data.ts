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

export type ChartSpec = BarChartSpec | MetricSpec

export type TabBundle = {
  meta: ChartMeta
  charts: Record<string, ChartSpec>
}

export type SiteMeta = {
  site: { name: string; tagline: string }
  github_project: string
  methodology_blurb: string
  tabs: { id: string; label: string }[]
}

export const tabDataPath: Record<string, string> = {
  industry: '/data/industry.json',
  postgrad: '/data/postgrad.json',
  international: '/data/international.json',
  origins: '/data/origins.json',
}
