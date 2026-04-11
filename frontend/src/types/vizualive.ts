import type { ChartMeta } from './data'

export type VizualiveNode = {
  id: string
  label: string
  count: number
  subtitle?: string
  children?: VizualiveNode[]
}

export type VizualiveBundle = {
  meta: ChartMeta
  roots: VizualiveNode[]
}
