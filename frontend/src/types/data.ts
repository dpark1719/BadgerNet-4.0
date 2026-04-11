import { publicPath } from '../publicPath'

export type ChartMeta = {
  project: string
  tab: string
  major_id?: string
  /** Dropdown label for Industry major slices; ETL may also emit `major_label`. */
  major_display_name?: string
  major_label?: string
  major_cip?: string
  cip?: string
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

export type SankeyNodeSpec = {
  id: string
  label: string
}

export type SankeyLinkSpec = {
  source: string
  target: string
  value: number
}

export type SankeyChartSpec = {
  type: 'sankey'
  title: string
  nodes: SankeyNodeSpec[]
  links: SankeyLinkSpec[]
}

export type ChartSpec =
  | BarChartSpec
  | MetricSpec
  | TrendChartSpec
  | SankeyChartSpec

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

export type MajorInfo = {
  id: string
  label: string
  cip?: string
}

export type MajorIndex = {
  majors: MajorInfo[]
}

export type Notability = 'widely_cited' | 'senior_role' | 'other'

export type NotableSourceType =
  | 'wikipedia'
  | 'uw_news'
  | 'linkedin_aggregate'
  | 'other'

export type NotableEntry = {
  name: string
  role_title: string
  organization: string
  field?: string
  graduation_year?: string | null
  degree_status?: string
  notability: Notability
  source_url: string
  source_type: NotableSourceType
  year?: string
  /** Portrait (Wikipedia/Wikidata Commons or site-relative path). */
  photo_url?: string
  /** Organization logo (e.g. Clearbit); shown when no portrait or as fallback. */
  logo_url?: string
  /** Small badge (e.g. Nobel, founder, company) — path under `public/`. */
  achievement_image_url?: string
  achievement_label?: string
}

export type NotableBundle = {
  meta: ChartMeta
  entries: NotableEntry[]
}

export const tabDataPath: Record<string, string> = {
  industry: publicPath('data/industry.json'),
  postgrad: publicPath('data/postgrad.json'),
  international: publicPath('data/international.json'),
  origins_undergrad: publicPath('data/origins_undergrad.json'),
  origins_graduate: publicPath('data/origins_graduate.json'),
  origins_doctorate: publicPath('data/origins_doctorate.json'),
  notable_alumni: publicPath('data/notable.json'),
}

export const majorsIndexPath = publicPath('data/majors/index.json')

export const majorAwareTabs = new Set<string>(['industry'])

export function majorSlicePath(majorId: string): string {
  return publicPath(`data/majors/${majorId}.json`)
}
