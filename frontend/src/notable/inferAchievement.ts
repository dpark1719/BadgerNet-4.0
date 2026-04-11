/**
 * Client-side fallback when JSON omits achievement_image_url.
 * Keep keyword order aligned with backend/lib/notable_enrichment.py.
 */
export function inferAchievementBadge(
  roleTitle: string,
  organization: string,
): { url: string; label: string } | null {
  const text = `${roleTitle} ${organization}`.toLowerCase()
  if (text.includes('nobel')) return achievement('notable/badge-nobel.svg', 'Nobel Prize')
  if (text.includes('pulitzer'))
    return achievement('notable/badge-pulitzer.svg', 'Pulitzer Prize')
  if (text.includes('olympic') || text.includes('olympian'))
    return achievement('notable/badge-olympic.svg', 'Olympic Games')
  if (text.includes('oscar') || text.includes('academy award'))
    return achievement('notable/badge-arts.svg', 'Academy Award')
  if (
    /\bco[- ]?founder\b/i.test(roleTitle + organization) ||
    /\bfounder\b/i.test(text) ||
    text.includes('entrepreneur')
  )
    return achievement('notable/badge-founder.svg', 'Founder / entrepreneur')
  if (/\bceo\b/i.test(text) || text.includes('chief executive'))
    return achievement('notable/badge-exec.svg', 'Executive leadership')
  if (text.includes('architect') || text.includes('architecture'))
    return achievement('notable/badge-architecture.svg', 'Architecture')
  if (text.includes('aviat') || text.includes('pilot') || text.includes('aviation'))
    return achievement('notable/badge-aviation.svg', 'Aviation')
  const org = organization.trim()
  if (org && !['—', '-', '–', 'n/a'].includes(org.toLowerCase()))
    return achievement('notable/company-generic.svg', 'Organization')
  return null
}

function achievement(path: string, label: string) {
  return { url: path, label }
}
