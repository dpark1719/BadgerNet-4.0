import { useState } from 'react'
import type { NotableBundle, NotableEntry } from '../types/data'
import { publicPath } from '../publicPath'
import { inferAchievementBadge } from '../notable/inferAchievement'

function resolvePhotoSrc(url: string | undefined): string | undefined {
  if (!url) return undefined
  if (/^https?:\/\//i.test(url)) return url
  return publicPath(url.replace(/^\/+/, ''))
}

function resolveAchievementSrc(url: string): string {
  if (/^https?:\/\//i.test(url)) return url
  return publicPath(url.replace(/^\/+/, ''))
}

function notabilityLabel(n: NotableEntry['notability']): string {
  switch (n) {
    case 'widely_cited':
      return 'Widely cited'
    case 'senior_role':
      return 'Senior role'
    default:
      return 'Other'
  }
}

const FIELD_COLORS: Record<string, string> = {
  'Electrical engineering': '#e07020',
  Biochemistry: '#2e8b57',
  'Genetics / microbiology': '#3a9a6e',
  'Biochemistry / genetics': '#3a9a6e',
  Physics: '#4a6cf7',
  'Agricultural economics': '#7a8b3d',
  Chemistry: '#c04080',
  'Mathematical physics': '#5a5af7',
  Biophysics: '#2a7a9a',
  'Aerospace / military': '#3060c0',
  'Medicine / aerospace': '#3070b0',
  'Organic chemistry': '#c06080',
  'Performing arts': '#b050a0',
  Literature: '#8060b0',
  'Literature / creative writing': '#8060b0',
  'Visual arts': '#c07040',
  'Economics / finance': '#5a8040',
  'Law / trade policy': '#6a6a80',
  'Diplomacy / political science': '#5a6a90',
  'Law / politics': '#6a6a80',
  'Literature / public policy': '#7a6090',
  'Soil science / politics': '#6a8a4a',
  'Architecture / politics': '#8a7060',
  Psychology: '#9a5a7a',
  'Biology / evolution': '#3a8a6a',
  Linguistics: '#7a7a50',
  'Organic chemistry / pharma': '#b06070',
  'Computer science': '#4a80c0',
  'Law / economics': '#6a7a7a',
  'Wrestling / athletics': '#c04040',
  'Biochemistry / endocrinology': '#3a8a5a',
}

function fieldColor(field?: string): string {
  if (!field) return '#888'
  return FIELD_COLORS[field] ?? '#888'
}

function orgInitials(org: string): string {
  if (!org || org === '—') return '?'
  return (
    org
      .split(/[\s/]+/)
      .filter((w) => w.length > 0 && w[0] === w[0].toUpperCase())
      .slice(0, 2)
      .map((w) => w[0])
      .join('')
      .toUpperCase() || org[0].toUpperCase()
  )
}

function achievementForEntry(entry: NotableEntry): { url: string; label: string } | null {
  if (entry.achievement_image_url && entry.achievement_label) {
    return {
      url: entry.achievement_image_url,
      label: entry.achievement_label,
    }
  }
  if (entry.achievement_image_url) {
    return { url: entry.achievement_image_url, label: 'Achievement' }
  }
  return inferAchievementBadge(entry.role_title, entry.organization)
}

function NotablePhotoBlock({ entry, color }: { entry: NotableEntry; color: string }) {
  const [photoFailed, setPhotoFailed] = useState(false)
  const [logoFailed, setLogoFailed] = useState(false)
  const resolvedPhoto = resolvePhotoSrc(entry.photo_url)
  const logoUrl = entry.logo_url?.trim()
  const placeholder = publicPath('notable/placeholder-person.svg')
  const achievement = achievementForEntry(entry)

  let src = placeholder
  let photoClass = 'notable-photo notable-photo--placeholder'
  let referrerPolicy: 'no-referrer' | undefined

  if (resolvedPhoto && !photoFailed) {
    src = resolvedPhoto
    photoClass = 'notable-photo'
    referrerPolicy = 'no-referrer'
  } else if (logoUrl && !logoFailed) {
    src = logoUrl
    photoClass = 'notable-photo notable-photo--logo'
  } else {
    src = placeholder
    photoClass = 'notable-photo notable-photo--placeholder'
  }

  const showAvatarFallback =
    photoFailed && (!logoUrl || logoFailed) && !resolvedPhoto

  if (showAvatarFallback) {
    return (
      <div className="notable-photo-stack">
        <div
          className="notable-avatar notable-avatar--large"
          style={{ background: color }}
          aria-hidden
        >
          {orgInitials(entry.organization)}
        </div>
        {achievement && (
          <span
            className="notable-achievement-badge"
            title={achievement.label}
            aria-label={achievement.label}
          >
            <img
              src={resolveAchievementSrc(achievement.url)}
              alt=""
              width={26}
              height={26}
              loading="lazy"
              decoding="async"
            />
          </span>
        )}
      </div>
    )
  }

  return (
    <div className="notable-photo-stack">
      <img
        src={src}
        alt=""
        className={photoClass}
        width={64}
        height={64}
        loading="lazy"
        decoding="async"
        referrerPolicy={referrerPolicy}
        onError={() => {
          if (resolvedPhoto && !photoFailed) {
            setPhotoFailed(true)
            return
          }
          if (logoUrl && !logoFailed) setLogoFailed(true)
        }}
      />
      {achievement && (
        <span
          className="notable-achievement-badge"
          title={achievement.label}
          aria-label={achievement.label}
        >
          <img
            src={resolveAchievementSrc(achievement.url)}
            alt=""
            width={26}
            height={26}
            loading="lazy"
            decoding="async"
          />
        </span>
      )}
    </div>
  )
}

export function NotablePanel({ bundle }: { bundle: NotableBundle }) {
  const [search, setSearch] = useState('')
  const [filterField, setFilterField] = useState('all')

  const allFields = Array.from(
    new Set(bundle.entries.map((e) => e.field).filter(Boolean)),
  ).sort() as string[]

  const filtered = bundle.entries.filter((entry) => {
    const matchSearch =
      !search ||
      entry.name.toLowerCase().includes(search.toLowerCase()) ||
      (entry.organization ?? '').toLowerCase().includes(search.toLowerCase()) ||
      (entry.field ?? '').toLowerCase().includes(search.toLowerCase())
    const matchField = filterField === 'all' || entry.field === filterField
    return matchSearch && matchField
  })

  return (
    <section className="notable-list" aria-label="Notable alumni">
      <div className="notable-controls">
        <input
          type="search"
          className="notable-search"
          placeholder="Search alumni, org, field…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search notable alumni"
        />
        <select
          className="notable-filter"
          value={filterField}
          onChange={(e) => setFilterField(e.target.value)}
          aria-label="Filter by field"
        >
          <option value="all">All fields</option>
          {allFields.map((f) => (
            <option key={f} value={f}>
              {f}
            </option>
          ))}
        </select>
        <span className="notable-count muted small">
          {filtered.length} of {bundle.entries.length}
        </span>
      </div>

      <ul className="notable-cards">
        {filtered.map((entry, i) => {
          const color = fieldColor(entry.field)
          return (
            <li key={`${entry.name}-${i}`} className="notable-card">
              <div className="notable-card-head">
                <NotablePhotoBlock entry={entry} color={color} />
                <div className="notable-header-text">
                  <h3 className="notable-name">{entry.name}</h3>
                  <p className="notable-role">{entry.role_title}</p>
                  {entry.organization && entry.organization !== '—' && (
                    <p className="notable-org">{entry.organization}</p>
                  )}
                </div>
              </div>

              <div className="notable-details">
                {entry.field && (
                  <span className="notable-detail">
                    <span className="notable-detail-label">Field</span>
                    <span
                      className="notable-detail-value"
                      style={{ color }}
                    >
                      {entry.field}
                    </span>
                  </span>
                )}
                {entry.degree_status && (
                  <span className="notable-detail">
                    <span className="notable-detail-label">Degree</span>
                    <span className="notable-detail-value">
                      {entry.degree_status}
                    </span>
                  </span>
                )}
                {entry.graduation_year && (
                  <span className="notable-detail">
                    <span className="notable-detail-label">Year</span>
                    <span className="notable-detail-value">
                      {entry.graduation_year}
                    </span>
                  </span>
                )}
                {!entry.graduation_year &&
                  entry.degree_status?.toLowerCase().includes('did not') && (
                    <span className="notable-detail">
                      <span className="notable-detail-label">Status</span>
                      <span className="notable-detail-value notable-dropout">
                        Did not graduate
                      </span>
                    </span>
                  )}
              </div>

              <div className="notable-meta">
                <span className="notable-tag">{notabilityLabel(entry.notability)}</span>
                <a
                  href={entry.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="notable-tag notable-tag--link"
                >
                  Wikipedia ↗
                </a>
              </div>
            </li>
          )
        })}
      </ul>

      {filtered.length === 0 && (
        <p className="muted" style={{ textAlign: 'center', padding: '2rem 0' }}>
          No alumni match your search.
        </p>
      )}
    </section>
  )
}
