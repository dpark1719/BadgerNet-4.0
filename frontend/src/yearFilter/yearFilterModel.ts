import type { ChartSpec, TabBundle } from '../types/data'

function trendRowYear(
  row: Record<string, string | number | undefined>,
  xKey: string,
): string {
  const v = row[xKey]
  return v === undefined || v === null ? '' : String(v)
}

/** Union of cohort years from `by_year` maps and trend `x_key` values. */
export function collectChartYears(bundle: TabBundle): string[] {
  const s = new Set<string>()
  for (const spec of Object.values(bundle.charts)) {
    if (spec.type === 'bar') {
      for (const row of spec.data) {
        if (row.by_year) {
          Object.keys(row.by_year).forEach((y) => s.add(y))
        }
      }
    }
    if (spec.type === 'sankey') {
      for (const L of spec.links) {
        if (L.by_year) Object.keys(L.by_year).forEach((y) => s.add(y))
      }
    }
    if (spec.type === 'metric' && spec.by_year) {
      Object.keys(spec.by_year).forEach((y) => s.add(y))
    }
    if (spec.type === 'trend') {
      const xk = spec.x_key ?? 'year'
      for (const row of spec.data) {
        const y = trendRowYear(row, xk)
        if (y) s.add(y)
      }
    }
  }
  return [...s].sort((a, b) => Number(a) - Number(b))
}

export function applyYearFilter(
  bundle: TabBundle,
  selectedYears: Set<string>,
): TabBundle {
  const charts: Record<string, ChartSpec> = {}
  for (const [key, spec] of Object.entries(bundle.charts)) {
    if (spec.type === 'bar') {
      charts[key] = {
        ...spec,
        data: spec.data.map((row) => {
          if (!row.by_year) return row
          let v = 0
          for (const y of selectedYears) {
            const part = row.by_year[y]
            if (part !== undefined) v += part
          }
          return { ...row, value: Math.round(v) }
        }),
      }
      continue
    }
    if (spec.type === 'sankey') {
      charts[key] = {
        ...spec,
        links: spec.links.map((L) => {
          if (!L.by_year) return L
          let v = 0
          for (const y of selectedYears) {
            const part = L.by_year[y]
            if (part !== undefined) v += part
          }
          return { ...L, value: Math.round(v) }
        }),
      }
      continue
    }
    if (spec.type === 'metric' && spec.by_year) {
      const vals: number[] = []
      for (const y of selectedYears) {
        const p = spec.by_year[y]
        if (p !== undefined) vals.push(p)
      }
      const avg = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0
      charts[key] = {
        ...spec,
        value: Math.round(avg * 100) / 100,
      }
      continue
    }
    if (spec.type === 'trend') {
      const xk = spec.x_key ?? 'year'
      charts[key] = {
        ...spec,
        data: spec.data.filter((row) =>
          selectedYears.has(trendRowYear(row, xk)),
        ),
      }
      continue
    }
    charts[key] = spec
  }
  return { ...bundle, charts }
}
