/** Map bar chart country labels to `world-atlas` / Natural Earth `properties.name`. */

const ALIASES: Record<string, string> = {
  'United States': 'United States of America',
  USA: 'United States of America',
  US: 'United States of America',
  'Czech Republic': 'Czechia',
  'Ivory Coast': "Côte d'Ivoire",
  'Democratic Republic of the Congo': 'Dem. Rep. Congo',
  Congo: 'Congo',
  Russia: 'Russia',
  'South Korea': 'South Korea',
  'North Korea': 'North Korea',
  Taiwan: 'Taiwan',
  Vietnam: 'Vietnam',
  UK: 'United Kingdom',
  Britain: 'United Kingdom',
  'Great Britain': 'United Kingdom',
}

/** Build once from atlas feature collection. */
export function buildTopoNameSet(names: Iterable<string>): Set<string> {
  return new Set(names)
}

export function labelToTopoCountryName(
  label: string,
  topoNames: Set<string>,
): string | null {
  const raw = label.trim()
  if (!raw) return null
  const viaAlias = ALIASES[raw]
  if (viaAlias && topoNames.has(viaAlias)) return viaAlias
  if (topoNames.has(raw)) return raw
  const lower = raw.toLowerCase()
  for (const n of topoNames) {
    if (n.toLowerCase() === lower) return n
  }
  return null
}

export function isUnmappedCountryBucket(label: string): boolean {
  const s = label.trim().toLowerCase()
  if (!s) return true
  if (s === 'other' || s.startsWith('other ')) return true
  if (s.includes('foreign') && s.includes('aggregat')) return true
  if (s.includes('all, aggregated')) return true
  if (s.includes('not specified')) return true
  return false
}
