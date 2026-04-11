import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { geoInterpolate, geoNaturalEarth1, geoPath } from 'd3-geo'
import { select } from 'd3-selection'
import { zoom, zoomIdentity, type ZoomBehavior } from 'd3-zoom'
import { feature } from 'topojson-client'
import type { Feature, FeatureCollection, LineString } from 'geojson'
import type { GeometryCollection, Topology } from 'topojson-specification'
import countriesTopology from 'world-atlas/countries-110m.json'
import type { BarChartSpec, TabBundle } from '../types/data'
import { publicPath } from '../publicPath'
import { COUNTRY_LABEL_TO_LON_LAT } from '../world/countryCentroids'
import './WorldMapPanel.css'

const MADISON_LON_LAT: [number, number] = [-89.4012, 43.0731]
const VIEW_W = 960
const VIEW_H = 520

async function loadJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

function isBarChart(spec: unknown): spec is BarChartSpec {
  return (
    typeof spec === 'object' &&
    spec !== null &&
    (spec as BarChartSpec).type === 'bar' &&
    Array.isArray((spec as BarChartSpec).data)
  )
}

function destinationLonLat(label: string): [number, number] | null {
  if (label === 'Other') return null
  const p = COUNTRY_LABEL_TO_LON_LAT[label]
  return p ?? null
}

export default function WorldMapPanel() {
  const reactId = useId().replace(/[^a-zA-Z0-9]/g, '')
  const glowFilterId = `mapGlow-${reactId}`

  const svgRef = useRef<SVGSVGElement | null>(null)
  const zoomRef = useRef<ZoomBehavior<SVGSVGElement, unknown> | null>(null)
  const [zf, setZf] = useState(() => zoomIdentity)
  const [hoverCountry, setHoverCountry] = useState<string | null>(null)
  const [hoverArc, setHoverArc] = useState<string | null>(null)

  const [bundle, setBundle] = useState<
    | { status: 'loading' }
    | { status: 'ok'; data: TabBundle }
    | { status: 'err'; message: string }
  >({ status: 'loading' })

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const data = await loadJson<TabBundle>(
          publicPath('data/map_destinations.json'),
        )
        if (!cancelled) setBundle({ status: 'ok', data })
      } catch (e: unknown) {
        if (!cancelled) {
          setBundle({
            status: 'err',
            message: e instanceof Error ? e.message : String(e),
          })
        }
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    const el = svgRef.current
    if (!el) return

    const z = zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.8, 20])
      .on('zoom', (ev) => setZf(ev.transform))

    zoomRef.current = z
    const sel = select(el)
    sel.call(z)

    return () => {
      sel.on('.zoom', null)
      zoomRef.current = null
    }
  }, [bundle.status])

  const countriesFc = useMemo(() => {
    const topo = countriesTopology as unknown as Topology
    return feature(
      topo,
      topo.objects.countries as GeometryCollection,
    ) as FeatureCollection
  }, [])

  /** Same order as `destination_country` in map_destinations.json; values unchanged. */
  const destinationRows = useMemo(() => {
    if (bundle.status !== 'ok') return []
    const spec = bundle.data.charts.destination_country
    if (!isBarChart(spec)) return []
    return spec.data.map((d) => ({
      label: d.label,
      count: d.value,
      mapPoint: destinationLonLat(d.label),
    }))
  }, [bundle])

  const flowsMapped = useMemo(() => {
    return destinationRows
      .filter((r) => r.mapPoint !== null && r.count > 0)
      .map((r) => ({
        label: r.label,
        count: r.count,
        lonLat: r.mapPoint!,
      }))
  }, [destinationRows])

  const maxCount = useMemo(
    () =>
      flowsMapped.length ? Math.max(...flowsMapped.map((f) => f.count)) : 1,
    [flowsMapped],
  )

  const projection = useMemo(() => {
    return geoNaturalEarth1()
      .scale(160)
      .translate([VIEW_W / 2, VIEW_H / 2])
  }, [])

  const path = useMemo(() => geoPath(projection), [projection])

  const arcPaths = useMemo(() => {
    const sorted = [...flowsMapped].sort((a, b) => a.count - b.count)
    return sorted.map((f) => {
      const interpolate = geoInterpolate(MADISON_LON_LAT, f.lonLat)
      const coordinates: [number, number][] = Array.from(
        { length: 56 },
        (_, i) => interpolate(i / 55) as [number, number],
      )
      const line: LineString = { type: 'LineString', coordinates }
      const d = path(line) ?? ''
      const t = Math.sqrt(f.count / maxCount)
      const strokeWidth = 0.85 + t * 10
      const opacity = 0.22 + t * 0.68
      return { key: f.label, d, strokeWidth, opacity, count: f.count }
    })
  }, [flowsMapped, maxCount, path])

  const madisonXY = projection(MADISON_LON_LAT)
  const mx = madisonXY?.[0] ?? 0
  const my = madisonXY?.[1] ?? 0

  const chartTotal = useMemo(
    () => destinationRows.reduce((s, r) => s + r.count, 0),
    [destinationRows],
  )
  const mappedTotal = useMemo(
    () => flowsMapped.reduce((s, r) => s + r.count, 0),
    [flowsMapped],
  )
  const unmappedTotal = chartTotal - mappedTotal

  const resetView = () => {
    const el = svgRef.current
    const z = zoomRef.current
    if (!el || !z) return
    select(el).call(z.transform, zoomIdentity)
  }

  const zoomBy = (factor: number) => {
    const el = svgRef.current
    const z = zoomRef.current
    if (!el || !z) return
    select(el).call(z.scaleBy, factor)
  }

  return (
    <div className="world-map-embed">
      {bundle.status === 'loading' && (
        <p className="muted">Loading destination counts…</p>
      )}
      {bundle.status === 'err' && (
        <p className="banner error" role="alert">
          {bundle.message}
        </p>
      )}
      {bundle.status === 'ok' && (
        <>
          <section className="meta-strip map-meta" aria-label="Data context">
            <p className="methodology">{bundle.data.meta.methodology}</p>
            {bundle.data.meta.disclaimer && (
              <p className="disclaimer">{bundle.data.meta.disclaimer}</p>
            )}
          </section>

          <div className="map-surface map-surface--interactive">
            <div className="map-glass map-legend" aria-label="Legend">
              <p className="map-legend-title">Map controls</p>
              <ul className="map-legend-list">
                <li>Scroll to zoom · drag to pan</li>
                <li>Hub: Madison, WI</li>
                <li>Thicker arc = more people</li>
              </ul>
              <div className="map-zoom-buttons">
                <button type="button" onClick={() => zoomBy(1.25)}>
                  Zoom in
                </button>
                <button type="button" onClick={() => zoomBy(1 / 1.25)}>
                  Zoom out
                </button>
                <button type="button" onClick={resetView}>
                  Reset view
                </button>
              </div>
            </div>

            <svg
              ref={svgRef}
              className="world-map-svg world-map-svg--zoom"
              viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}
              width="100%"
              height="auto"
              role="application"
              aria-label="Interactive world map: alumni flows from Madison"
            >
              <defs>
                <filter
                  id={glowFilterId}
                  x="-20%"
                  y="-20%"
                  width="140%"
                  height="140%"
                >
                  <feGaussianBlur stdDeviation="1.1" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>

              <g transform={zf.toString()} className="map-zoom-layer">
                <rect
                  className="map-ocean"
                  x={0}
                  y={0}
                  width={VIEW_W}
                  height={VIEW_H}
                />

                <g className="map-countries">
                  {countriesFc.features.map((f) => {
                    const name = (f.properties as { name?: string })?.name ?? ''
                    const isAntarctica = name === 'Antarctica'
                    const d = path(f as Feature) ?? ''
                    const isDestination = flowsMapped.some((fl) => fl.label === name)
                    const isHovered = hoverCountry === name
                    return (
                      <path
                        key={String(f.id ?? name ?? d.slice(0, 24))}
                        d={d}
                        className={
                          isAntarctica
                            ? 'country antarctica'
                            : isDestination
                              ? `country country--dest${isHovered ? ' country--hover' : ''}`
                              : 'country'
                        }
                        onMouseEnter={() => setHoverCountry(name)}
                        onMouseLeave={() => setHoverCountry(null)}
                      >
                        <title>{name}</title>
                      </path>
                    )
                  })}
                </g>

                <g
                  className="map-flows"
                  filter={`url(#${glowFilterId})`}
                >
                  {arcPaths.map((a) => (
                    <path
                      key={a.key}
                      d={a.d}
                      className={`flow-arc${hoverArc === a.key ? ' flow-arc--hover' : ''}`}
                      style={{
                        strokeWidth: hoverArc === a.key ? a.strokeWidth + 3 : a.strokeWidth,
                        opacity: hoverArc === a.key ? 1 : a.opacity,
                      }}
                      onMouseEnter={() => setHoverArc(a.key)}
                      onMouseLeave={() => setHoverArc(null)}
                    >
                      <title>{a.key}: {a.count} alumni</title>
                    </path>
                  ))}
                </g>

                <g className="map-dest-dots" style={{ pointerEvents: 'none' }}>
                  {flowsMapped.map((f) => {
                    const pt = projection(f.lonLat)
                    if (!pt) return null
                    const r = 2 + Math.sqrt(f.count / maxCount) * 4
                    return (
                      <circle
                        key={f.label}
                        cx={pt[0]}
                        cy={pt[1]}
                        r={r}
                        className="dest-dot"
                      />
                    )
                  })}
                </g>

                <g className="map-hub" style={{ pointerEvents: 'none' }}>
                  <circle className="hub-ring" cx={mx} cy={my} r={14} />
                  <circle className="hub-dot" cx={mx} cy={my} r={6} />
                  <text
                    className="hub-label"
                    x={mx + 14}
                    y={my - 8}
                    textAnchor="start"
                  >
                    Madison, WI
                  </text>
                </g>
              </g>
            </svg>
          </div>

          <section className="map-table" aria-label="Destination counts">
            <h2 className="map-table-title">
              Post-UW country (same data as bar chart)
            </h2>
            <p className="muted small map-table-lead">
              Counts are read directly from{' '}
              <code className="mono-inline">charts.destination_country</code> in{' '}
              <code className="mono-inline">map_destinations.json</code>. “Other” is
              an aggregate bucket with no single map point.
            </p>
            <div className="map-table-head map-table-row">
              <span>Destination</span>
              <span className="map-col-n">Count</span>
              <span className="map-col-map">On map</span>
            </div>
            <div className="map-table-body">
              {destinationRows.map((r) => (
                <div key={r.label} className="map-table-row">
                  <span>{r.label}</span>
                  <span className="mono map-col-n">{r.count}</span>
                  <span className="map-col-map">
                    {r.mapPoint ? 'Yes' : 'No'}
                  </span>
                </div>
              ))}
            </div>
            <div className="map-table-summary">
              <span>Total (all rows)</span>
              <span className="mono">{chartTotal}</span>
              <span />
            </div>
            <div className="map-table-summary muted">
              <span>Sum of drawn arcs</span>
              <span className="mono">{mappedTotal}</span>
              <span />
            </div>
            {unmappedTotal > 0 && (
              <div className="map-table-summary muted">
                <span>Not drawn (Other + any unmapped)</span>
                <span className="mono">{unmappedTotal}</span>
                <span />
              </div>
            )}
          </section>
        </>
      )}
    </div>
  )
}
