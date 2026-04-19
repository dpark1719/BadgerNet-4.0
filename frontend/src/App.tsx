import { useCallback, useEffect, useMemo, useState } from 'react'
import { renderChart } from './components/ChartPanels'
import LandingPage from './components/LandingPage'
import { NotablePanel } from './components/NotablePanel'
import VisualizePanel from './components/VizualivePanel'
import { DataSourcesPanel } from './components/DataSourcesPanel'
import { OriginsMaps } from './components/OriginsMaps'
import { YearFilterBar } from './components/YearFilterBar'
import WorldMapPanel from './components/WorldMapPanel'
import { RankingsHubPanel } from './components/RankingsHubPanel'
import type { MajorIndex, NotableBundle, RankingsHubBundle, SiteMeta, TabBundle } from './types/data'
import {
  majorAwareTabs,
  majorSlicePath,
  majorsIndexPath,
  tabDataPath,
} from './types/data'
import { publicPath } from './publicPath'
import { applyYearFilter, collectChartYears } from './yearFilter/yearFilterModel'
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
  | { status: 'ok'; mode: 'datasources' }
  | { status: 'ok'; mode: 'rankings'; data: RankingsHubBundle }

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

function readYearsParam(): string[] {
  const raw = new URLSearchParams(window.location.search).get('years')
  if (!raw) return []
  return raw
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
}

function syncTabQueryParam(activeTab: string, defaultTab: string) {
  const u = new URL(window.location.href)
  if (activeTab === defaultTab) u.searchParams.delete('tab')
  else u.searchParams.set('tab', activeTab)
  window.history.replaceState(null, '', `${u.pathname}${u.search}${u.hash}`)
}

function syncYearsQueryParam(
  selectedYears: Set<string>,
  allYears: string[],
) {
  const u = new URL(window.location.href)
  const full =
    allYears.length > 0 &&
    selectedYears.size === allYears.length &&
    allYears.every((y) => selectedYears.has(y))
  if (full || selectedYears.size === 0 || allYears.length === 0) {
    u.searchParams.delete('years')
  } else {
    u.searchParams.set(
      'years',
      [...selectedYears].sort((a, b) => Number(a) - Number(b)).join(','),
    )
  }
  window.history.replaceState(null, '', `${u.pathname}${u.search}${u.hash}`)
}

function initialTabFromUrl(): string {
  try {
    return new URLSearchParams(window.location.search).get('tab') || 'industry'
  } catch {
    return 'industry'
  }
}

export default function App() {
  const [showLanding, setShowLanding] = useState(true)
  const [site, setSite] = useState<LoadState<SiteMeta>>({ status: 'loading' })
  const [majors, setMajors] = useState<LoadState<MajorIndex>>({
    status: 'loading',
  })
  const [activeTab, setActiveTab] = useState<string>(initialTabFromUrl)
  const [majorId, setMajorId] = useState<string>('all')
  const [view, setView] = useState<ViewState>({ status: 'loading' })
  const [methodOpen, setMethodOpen] = useState(false)
  const [selectedYears, setSelectedYears] = useState<Set<string>>(new Set())

  useEffect(() => {
    let cancelled = false
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
    if (majors.status !== 'ok') return
    let cancelled = false
    const raw = new URLSearchParams(window.location.search).get('major')
    if (raw && majors.data.majors.some((m) => m.id === raw)) {
      void Promise.resolve().then(() => {
        if (!cancelled) setMajorId(raw)
      })
    }
    return () => {
      cancelled = true
    }
  }, [majors])

  useEffect(() => {
    if (site.status !== 'ok') return
    let cancelled = false
    const allowed = new Set(site.data.tabs.map((t) => t.id))
    if (!allowed.has(activeTab)) {
      const fallback = site.data.tabs[0]?.id ?? 'industry'
      void Promise.resolve().then(() => {
        if (!cancelled) setActiveTab(fallback)
      })
    }
    return () => {
      cancelled = true
    }
  }, [site, activeTab])

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
      if (activeTab === 'data_sources') {
        if (!cancelled) setView({ status: 'ok', mode: 'datasources' })
        return
      }
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
        if (activeTab === 'rankings') {
          const data = await loadJson<RankingsHubBundle>(url)
          if (!cancelled) setView({ status: 'ok', mode: 'rankings', data })
          return
        }
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

  const chartsFingerprint = useMemo(() => {
    if (view.status !== 'ok' || view.mode !== 'charts') return ''
    const m = view.data.meta
    return `${activeTab}|${majorId}|${m.snapshot_date}|${m.tab}|${m.filter_fingerprint ?? ''}`
  }, [view, activeTab, majorId])

  useEffect(() => {
    if (!chartsFingerprint) return
    if (view.status !== 'ok' || view.mode !== 'charts') return
    let cancelled = false
    const opts = collectChartYears(view.data)
    void Promise.resolve().then(() => {
      if (cancelled) return
      if (opts.length === 0) {
        setSelectedYears(new Set())
        return
      }
      const want = readYearsParam()
      if (want.length > 0) {
        const sel = new Set(opts.filter((y) => want.includes(y)))
        if (sel.size > 0) {
          setSelectedYears(sel)
          return
        }
      }
      setSelectedYears(new Set(opts))
    })
    return () => {
      cancelled = true
    }
  }, [chartsFingerprint, view])

  const chartYearOptions = useMemo(() => {
    if (view.status !== 'ok' || view.mode !== 'charts') return []
    return collectChartYears(view.data)
  }, [view])

  useEffect(() => {
    if (site.status !== 'ok') return
    const defaultTab = site.data.tabs[0]?.id ?? 'industry'
    syncTabQueryParam(activeTab, defaultTab)
  }, [activeTab, site])

  useEffect(() => {
    if (chartYearOptions.length === 0) return
    syncYearsQueryParam(selectedYears, chartYearOptions)
  }, [selectedYears, chartYearOptions])

  const chartsBundle = useMemo(() => {
    if (view.status !== 'ok' || view.mode !== 'charts') return null
    const all = collectChartYears(view.data)
    if (all.length === 0) return view.data
    if (selectedYears.size === 0) return view.data
    return applyYearFilter(view.data, selectedYears)
  }, [view, selectedYears])

  const toggleChartYear = useCallback((y: string) => {
    setSelectedYears((prev) => {
      const next = new Set(prev)
      if (next.has(y)) {
        if (next.size <= 1) return next
        next.delete(y)
      } else {
        next.add(y)
      }
      return next
    })
  }, [])

  const selectAllChartYears = useCallback(() => {
    if (view.status !== 'ok' || view.mode !== 'charts') return
    setSelectedYears(new Set(collectChartYears(view.data)))
  }, [view])

  const isOriginsTab = activeTab.startsWith('origins_')

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
    (view.mode === 'worldmap' ||
      view.mode === 'visualize' ||
      view.mode === 'rankings')
      ? ' main--wide'
      : ''

  if (showLanding) {
    return <LandingPage onEnter={() => setShowLanding(false)} />
  }

  return (
    <div className="app">
      <div className="app-branding">
        <div className="uw-banner-overlay" aria-label="University branding">
          <div className="uw-banner-strip">
            <span className="uw-banner-mark" aria-hidden="true">
              W
            </span>
            <div className="uw-banner-text">
              <span className="uw-banner-title">University of Wisconsin–Madison</span>
              <span className="uw-banner-tag">Official alumni outcomes explorer</span>
            </div>
          </div>
        </div>
        <img
          className="uw-bucky-image"
          src={publicPath('brand/bucky-badger.svg')}
          alt="Bucky Badger mascot illustration"
          width={112}
          height={140}
          decoding="async"
        />
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
      </div>

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
            onClick={() => {
              setActiveTab(t.id)
            }}
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
        {view.status === 'ok' && view.mode === 'datasources' && site.status === 'ok' && (
          <DataSourcesPanel site={site.data} />
        )}
        {view.status === 'ok' && view.mode === 'worldmap' && <WorldMapPanel />}
        {view.status === 'ok' && view.mode === 'visualize' && <VisualizePanel />}
        {view.status === 'ok' && view.mode === 'rankings' && (
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
                    Primary source (Wikidata)
                  </a>
                </p>
              )}
              {view.data.meta.disclaimer && (
                <p className="disclaimer">{view.data.meta.disclaimer}</p>
              )}
            </section>
            <RankingsHubPanel bundle={view.data} />
          </>
        )}
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
        {view.status === 'ok' && view.mode === 'charts' && chartsBundle && (
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
              {chartYearOptions.length > 0 &&
                selectedYears.size < chartYearOptions.length && (
                  <p className="year-filter-hint muted small">
                    Charts reflect the selected cohort years only (multi-select).
                  </p>
                )}
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

            {chartYearOptions.length > 0 && (
              <YearFilterBar
                years={chartYearOptions}
                selected={selectedYears}
                onToggle={toggleChartYear}
                onSelectAll={selectAllChartYears}
              />
            )}

            {isOriginsTab && <OriginsMaps bundle={chartsBundle} />}

            <section className="charts" aria-label="Charts">
              {Object.entries(chartsBundle.charts).map(([key, spec]) =>
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
  { id: 'outcomes_scorecard', label: 'Peer outcomes' },
  { id: 'research_openalex', label: 'Research footprint' },
  { id: 'rankings', label: 'Rankings' },
  { id: 'data_sources', label: 'Data catalog' },
]
