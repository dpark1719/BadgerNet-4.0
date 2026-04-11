import { useCallback, useEffect, useState } from 'react'
import { renderChart } from './components/ChartPanels'
import type { SiteMeta, TabBundle } from './types/data'
import { tabDataPath } from './types/data'
import './App.css'

type LoadState<T> =
  | { status: 'idle' | 'loading' }
  | { status: 'ok'; data: T }
  | { status: 'err'; message: string }

async function loadJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export default function App() {
  const [site, setSite] = useState<LoadState<SiteMeta>>({ status: 'idle' })
  const [activeTab, setActiveTab] = useState<string>('industry')
  const [bundle, setBundle] = useState<LoadState<TabBundle>>({ status: 'idle' })
  const [methodOpen, setMethodOpen] = useState(false)

  useEffect(() => {
    let cancelled = false
    setSite({ status: 'loading' })
    loadJson<SiteMeta>('/data/meta.json')
      .then((data) => {
        if (!cancelled) setSite({ status: 'ok', data })
      })
      .catch((e: Error) => {
        if (!cancelled) setSite({ status: 'err', message: e.message })
      })
    return () => {
      cancelled = true
    }
  }, [])

  const loadTab = useCallback((tabId: string) => {
    const path = tabDataPath[tabId]
    if (!path) return
    setBundle({ status: 'loading' })
    loadJson<TabBundle>(path)
      .then((data) => setBundle({ status: 'ok', data }))
      .catch((e: Error) => setBundle({ status: 'err', message: e.message }))
  }, [])

  useEffect(() => {
    loadTab(activeTab)
  }, [activeTab, loadTab])

  const siteName =
    site.status === 'ok' ? site.data.site.name : 'BadgerNet 4.0'
  const tagline =
    site.status === 'ok'
      ? site.data.site.tagline
      : 'Loading UW–Madison outcomes…'
  const tabs = site.status === 'ok' ? site.data.tabs : []
  const methodology =
    site.status === 'ok' ? site.data.methodology_blurb : ''
  const ghProject =
    site.status === 'ok' ? site.data.github_project : ''

  return (
    <div className="app">
      <header className="header">
        <div className="header-text">
          <p className="eyebrow">University of Wisconsin–Madison</p>
          <h1>{siteName}</h1>
          <p className="tagline">{tagline}</p>
        </div>
      </header>

      {site.status === 'err' && (
        <p className="banner error" role="alert">
          Could not load site metadata: {site.message}
        </p>
      )}

      <nav className="tabs" aria-label="Data views">
        {(tabs.length ? tabs : fallbackTabs).map((t) => (
          <button
            key={t.id}
            type="button"
            className={t.id === activeTab ? 'tab active' : 'tab'}
            onClick={() => setActiveTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="main">
        {bundle.status === 'loading' && (
          <p className="muted">Loading tab data…</p>
        )}
        {bundle.status === 'err' && (
          <p className="banner error" role="alert">
            {bundle.message}
          </p>
        )}
        {bundle.status === 'ok' && (
          <>
            <section className="meta-strip" aria-label="Data context">
              <div className="meta-grid">
                <div>
                  <span className="meta-label">Snapshot</span>
                  <span className="meta-value">
                    {bundle.data.meta.snapshot_date}
                  </span>
                </div>
                <div>
                  <span className="meta-label">Degree level</span>
                  <span className="meta-value">
                    {bundle.data.meta.degree_level}
                  </span>
                </div>
                <div>
                  <span className="meta-label">Source</span>
                  <span className="meta-value">{bundle.data.meta.source}</span>
                </div>
                {bundle.data.meta.academic_year && (
                  <div>
                    <span className="meta-label">Academic year</span>
                    <span className="meta-value">
                      {bundle.data.meta.academic_year}
                    </span>
                  </div>
                )}
              </div>
              <p className="methodology">{bundle.data.meta.methodology}</p>
              {bundle.data.meta.source_url && (
                <p>
                  <a
                    className="link"
                    href={bundle.data.meta.source_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Primary source
                  </a>
                </p>
              )}
              {bundle.data.meta.disclaimer && (
                <p className="disclaimer">{bundle.data.meta.disclaimer}</p>
              )}
            </section>

            <section className="charts" aria-label="Charts">
              {Object.entries(bundle.data.charts).map(([key, spec]) =>
                renderChart(key, spec),
              )}
            </section>
          </>
        )}
      </main>

      <footer className="footer">
        <button
          type="button"
          className="link-button"
          onClick={() => setMethodOpen((o) => !o)}
          aria-expanded={methodOpen}
        >
          {methodOpen ? 'Hide' : 'Show'} methodology &amp; collaboration
        </button>
        {methodOpen && (
          <div className="footer-panel">
            <p>{methodology}</p>
            {ghProject && (
              <p>
                <a className="link" href={ghProject}>
                  GitHub Project board
                </a>
              </p>
            )}
            <p className="muted small">
              Backend: David · Frontend: Rohan — see CONTRIBUTING.md in the
              repository root.
            </p>
          </div>
        )}
      </footer>
    </div>
  )
}

const fallbackTabs = [
  { id: 'industry', label: 'Industry' },
  { id: 'postgrad', label: 'Post-grad education' },
  { id: 'international', label: 'International outcomes' },
  { id: 'origins', label: 'Student origins' },
]
