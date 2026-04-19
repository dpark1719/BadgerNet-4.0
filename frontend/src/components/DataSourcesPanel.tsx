import { useEffect, useState } from 'react'
import type { SiteMeta, SourcesIndex } from '../types/data'
import { publicPath } from '../publicPath'
import './DataSourcesPanel.css'

async function loadJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

type LoadState<T> =
  | { status: 'loading' }
  | { status: 'ok'; data: T }
  | { status: 'err'; message: string }

export function DataSourcesPanel({ site }: { site: SiteMeta }) {
  const [index, setIndex] = useState<LoadState<SourcesIndex>>({
    status: 'loading',
  })

  useEffect(() => {
    let cancelled = false
    loadJson<SourcesIndex>(publicPath('data/sources_index.json'))
      .then((data) => {
        if (!cancelled) setIndex({ status: 'ok', data })
      })
      .catch((e: Error) => {
        if (!cancelled) setIndex({ status: 'err', message: e.message })
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <section className="sources-panel" aria-labelledby="sources-heading">
      <h2 id="sources-heading" className="sources-heading">
        Data catalog
      </h2>
      <p className="sources-lead">{site.methodology_blurb}</p>

      {index.status === 'loading' && (
        <p className="muted">Loading bundle index…</p>
      )}
      {index.status === 'err' && (
        <p className="banner error" role="alert">
          Could not load sources index: {index.message}
        </p>
      )}
      {index.status === 'ok' && (
        <>
          <p className="muted small sources-meta">
            Index snapshot: {index.data.snapshot_date ?? '—'}
          </p>
          <ul className="sources-list">
            {index.data.bundles.map((b) => (
              <li key={b.tab_id} className="sources-card">
                <div className="sources-card-head">
                  <h3 className="sources-card-title">{b.label}</h3>
                  <span
                    className={
                      b.file_exists ? 'sources-pill sources-pill--ok' : 'sources-pill'
                    }
                  >
                    {b.file_exists ? 'Present' : 'Missing'}
                  </span>
                </div>
                <p className="sources-path mono small">
                  {b.relative_path ? `/data/${b.relative_path}` : '— (site navigation only)'}
                </p>
                <dl className="sources-dl">
                  <div>
                    <dt>Tab id</dt>
                    <dd className="mono">{b.tab_id}</dd>
                  </div>
                  {b.snapshot_date && (
                    <div>
                      <dt>Bundle snapshot</dt>
                      <dd>{b.snapshot_date}</dd>
                    </div>
                  )}
                  {b.source && (
                    <div>
                      <dt>Source tag</dt>
                      <dd>{b.source}</dd>
                    </div>
                  )}
                </dl>
                {b.methodology && (
                  <details className="sources-details">
                    <summary>Methodology</summary>
                    <p className="sources-methodology">{b.methodology}</p>
                  </details>
                )}
                {b.disclaimer && (
                  <p className="sources-disclaimer small">{b.disclaimer}</p>
                )}
              </li>
            ))}
          </ul>
          <ul className="sources-notes muted small">
            {index.data.notes.map((n) => (
              <li key={n}>{n}</li>
            ))}
          </ul>
        </>
      )}
    </section>
  )
}
