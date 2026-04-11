import { useCallback, useEffect, useRef, useState } from 'react'
import { renderChart } from './components/ChartPanels'
import LandingPage from './components/LandingPage'
import { NotablePanel } from './components/NotablePanel'
import VisualizePanel from './components/VizualivePanel'
import WorldMapPanel from './components/WorldMapPanel'
import type { MajorIndex, NotableBundle, SiteMeta, TabBundle } from './types/data'
import {
  majorAwareTabs,
  majorSlicePath,
  majorsIndexPath,
  tabDataPath,
} from './types/data'
import { publicPath } from './publicPath'
import './App.css'

type LoadState<T> =
  | { status: 'idle' | 'loading' }
  | { status: 'ok'; data: T }
  | { status: 'err'; message: string }

type ViewState =
  | { status: 'idle' | 'loading' }
  | { status: 'err'; message: string }
  | { status: 'ok'; mode: 'charts'; data: TabBundle }
  | { status: 'ok'; mode: 'notable'; data: NotableBundle }
  | { status: 'ok'; mode: 'worldmap' }
  | { status: 'ok'; mode: 'visualize' }

async function loadJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

function syncMajorQueryParam(majorId: string) {
  const u = new URL(window.location.href)
  if (majorId === 'all') u.searchParams.delete('major')
  else u.searchParams.set('major', majorId)
  window.history.replaceState(null, '', `${u.pathname}${u.search}${u.hash}`)
}

export default function App() {
  const [showLanding, setShowLanding] = useState(true)
  const [site, setSite] = useState<LoadState<SiteMeta>>({ status: 'idle' })
  const [majors, setMajors] = useState<LoadState<MajorIndex>>({ status: 'idle' })
  const [activeTab, setActiveTab] = useState<string>('industry')
  const [majorId, setMajorId] = useState<string>('all')
  const [view, setView] = useState<ViewState>({ status: 'idle' })
  const [methodOpen, setMethodOpen] = useState(false)
  const majorInited = useRef(false)

  useEffect(() => {
    let cancelled = false
    setSite({ status: 'loading' })
    loadJson<SiteMeta>(publicPath('data/meta.json'))
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

  useEffect(() => {
    let cancelled = false
    setMajors({ status: 'loading' })
    loadJson<MajorIndex>(majorsIndexPath)
      .then((data) => {
        if (!cancelled) setMajors({ status: 'ok', data })
      })
      .catch((e: Error) => {
        if (!cancelled) setMajors({ status: 'err', message: e.message })
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (majors.status !== 'ok' || majorInited.current) return
    majorInited.current = true
    const raw = new URLSearchParams(window.location.search).get('major')
    if (raw && majors.data.majors.some((m) => m.id === raw)) {
      setMajorId(raw)
    }
  }, [majors])

  const resolveDataUrl = useCallback((tabId: string, major: string): string => {
    if (tabId === 'notable_alumni') {
      return tabDataPath.notable_alumni
    }
    if (majorAwareTabs.has(tabId) && major !== 'all') {
      return majorSlicePath(major)
    }
    const path = tabDataPath[tabId]
    if (!path) throw new Error(`Unknown tab: ${tabId}`)
    return path
  }, [])

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      if (activeTab === 'world_map') {
        if (!cancelled) setView({ status: 'ok', mode: 'worldmap' })
        return
      }
      if (activeTab === 'visualize') {
        if (!cancelled) setView({ status: 'ok', mode: 'visualize' })
        return
      }
      try {
        const url = resolveDataUrl(activeTab, majorId)
        if (!cancelled) setView({ status: 'loading' })
        if (activeTab === 'notable_alumni') {
          const data = await loadJson<NotableBundle>(url)
          if (!cancelled) setView({ status: 'ok', mode: 'notable', data })
        } else {
          const data = await loadJson<TabBundle>(url)
          if (!cancelled) setView({ status: 'ok', mode: 'charts', data })
        }
      } catch (e: unknown) {
        if (!cancelled) {
          setView({
            status: 'err',
            message: e instanceof Error ? e.message : String(e),
          })
        }
      }
    }
    void run()
    return () => {
      cancelled = true
    }
  }, [activeTab, majorId, resolveDataUrl])

  const onMajorChange = (id: string) => {
    setMajorId(id)
    syncMajorQueryParam(id)
  }

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
  const ghRepo = site.status === 'ok' ? site.data.github_repo : ''

  const majorOptions = majors.status === 'ok' ? majors.data.majors : []

  const mainWide =
    view.status === 'ok' &&
    (view.mode === 'worldmap' || view.mode === 'visualize')
      ? ' main--wide'
      : ''

  if (showLanding) {
    return <LandingPage onEnter={() => setShowLanding(false)} />
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-text">
          <p className="eyebrow">University of Wisconsin–Madison</p>
          <h1>{siteName}</h1>
          <p className="tagline">{tagline}</p>
        </div>
        {activeTab === 'industry' && majorOptions.length > 0 && (
          <div className="major-filter">
            <label htmlFor="major-select" className="major-filter-label">
              Filter by major
            </label>
            <select
              id="major-select"
              className="major-select"
              value={majorId}
              onChange={(e) => onMajorChange(e.target.value)}
            >
              <option value="all">All majors</option>
              {majorOptions.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.label}
                </option>
              ))}
            </select>
          </div>
        )}
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

      <main className={`main${mainWide}`}>
        {view.status === 'loading' && (
          <p className="muted">Loading tab data…</p>
        )}
        {view.status === 'err' && (
          <p className="banner error" role="alert">
            {view.message}
          </p>
        )}
        {view.status === 'ok' && view.mode === 'worldmap' && <WorldMapPanel />}
        {view.status === 'ok' && view.mode === 'visualize' && <VisualizePanel />}
        {view.status === 'ok' && view.mode === 'notable' && (
          <>
            <section className="meta-strip" aria-label="Data context">
              <div className="meta-grid">
                <div>
                  <span className="meta-label">Snapshot</span>
                  <span className="meta-value">
                    {view.data.meta.snapshot_date}
                  </span>
                </div>
                <div>
                  <span className="meta-label">Source</span>
                  <span className="meta-value">{view.data.meta.source}</span>
                </div>
                <div>
                  <span className="meta-label">Entries</span>
                  <span className="meta-value">
                    {view.data.entries.length}
                  </span>
                </div>
              </div>
              <p className="methodology">{view.data.meta.methodology}</p>
              {view.data.meta.disclaimer && (
                <p className="disclaimer">{view.data.meta.disclaimer}</p>
              )}
            </section>
            <NotablePanel bundle={view.data} />
          </>
        )}
        {view.status === 'ok' && view.mode === 'charts' && (
          <>
            <section className="meta-strip" aria-label="Data context">
              <div className="meta-grid">
                <div>
                  <span className="meta-label">Snapshot</span>
                  <span className="meta-value">
                    {view.data.meta.snapshot_date}
                  </span>
                </div>
                <div>
                  <span className="meta-label">Degree level</span>
                  <span className="meta-value">
                    {view.data.meta.degree_level}
                  </span>
                </div>
                <div>
                  <span className="meta-label">Source</span>
                  <span className="meta-value">{view.data.meta.source}</span>
                </div>
                {view.data.meta.major_id && (
                  <div>
                    <span className="meta-label">Major</span>
                    <span className="meta-value">{view.data.meta.major_id}</span>
                  </div>
                )}
                {view.data.meta.filter_fingerprint && (
                  <div className="meta-span-2">
                    <span className="meta-label">Filter fingerprint</span>
                    <span className="meta-value mono">
                      {view.data.meta.filter_fingerprint}
                    </span>
                  </div>
                )}
                {view.data.meta.academic_year && (
                  <div>
                    <span className="meta-label">Academic year</span>
                    <span className="meta-value">
                      {view.data.meta.academic_year}
                    </span>
                  </div>
                )}
              </div>
              <p className="methodology">{view.data.meta.methodology}</p>
              {view.data.meta.source_url && (
                <p>
                  <a
                    className="link"
                    href={view.data.meta.source_url}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Primary source
                  </a>
                </p>
              )}
              {view.data.meta.disclaimer && (
                <p className="disclaimer">{view.data.meta.disclaimer}</p>
              )}
            </section>

            <section className="charts" aria-label="Charts">
              {Object.entries(view.data.charts).map(([key, spec]) =>
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
            {ghRepo && (
              <p>
                <a className="link" href={ghRepo}>
                  Source repository
                </a>
              </p>
            )}
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
  { id: 'world_map', label: 'World map' },
  { id: 'visualize', label: 'Visualize' },
  { id: 'notable_alumni', label: 'Notable alumni' },
  { id: 'origins_undergrad', label: 'Origins — UG' },
  { id: 'origins_graduate', label: 'Origins — Grad' },
  { id: 'origins_doctorate', label: 'Origins — PhD' },
]
