import type { NotableBundle, NotableEntry } from '../types/data'
import { publicPath } from '../publicPath'

function resolvePhotoSrc(url: string | undefined): string | undefined {
  if (!url) return undefined
  if (/^https?:\/\//i.test(url)) return url
  if (url.startsWith('/')) return publicPath(url.replace(/^\/+/, ''))
  return url
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

function sourceLabel(t: NotableEntry['source_type']): string {
  switch (t) {
    case 'wikipedia':
      return 'Wikipedia'
    case 'uw_news':
      return 'UW / news'
    case 'linkedin_aggregate':
      return 'LinkedIn (reviewed aggregate)'
    default:
      return 'Source'
  }
}

export function NotablePanel({ bundle }: { bundle: NotableBundle }) {
  return (
    <section className="notable-list" aria-label="Notable alumni">
      <ul className="notable-cards">
        {bundle.entries.map((entry, i) => (
          <li key={`${entry.name}-${i}`} className="notable-card">
            <div className="notable-card-head">
              {entry.photo_url ? (
                <img
                  src={resolvePhotoSrc(entry.photo_url)}
                  alt=""
                  className="notable-photo"
                  width={56}
                  height={56}
                />
              ) : (
                <div className="notable-photo-placeholder" aria-hidden>
                  {entry.name.charAt(0)}
                </div>
              )}
              <div>
                <h3 className="notable-name">{entry.name}</h3>
                <p className="notable-role">
                  {entry.role_title}
                  {entry.organization ? ` · ${entry.organization}` : ''}
                </p>
              </div>
            </div>
            <div className="notable-meta">
              <span className="notable-tag">{notabilityLabel(entry.notability)}</span>
              <span className="notable-tag notable-tag--source">
                {sourceLabel(entry.source_type)}
              </span>
              {entry.year && (
                <span className="notable-year muted small">{entry.year}</span>
              )}
            </div>
            <p className="notable-source">
              <a
                href={entry.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="link"
              >
                Verify source
              </a>
            </p>
          </li>
        ))}
      </ul>
    </section>
  )
}
