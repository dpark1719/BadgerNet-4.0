import { useMemo, useState } from 'react'
import { geoAlbersUsa, geoNaturalEarth1, geoPath } from 'd3-geo'
import { feature } from 'topojson-client'
import type { FeatureCollection, GeoJSON, Geometry } from 'geojson'
import type { GeometryCollection, Topology } from 'topojson-specification'
import usStatesTopology from 'us-atlas/states-10m.json'
import countriesTopology from 'world-atlas/countries-110m.json'
import type { BarChartSpec, TabBundle } from '../types/data'
import {
  buildTopoNameSet,
  isUnmappedCountryBucket,
  labelToTopoCountryName,
} from '../origins/countryTopoMatch'
import './OriginsMaps.css'

const US_W = 560
const US_H = 340
const WORLD_W = 720
const WORLD_H = 360
const R = 197
const G = 5
const B = 12

function isBarChart(spec: unknown): spec is BarChartSpec {
  return (
    typeof spec === 'object' &&
    spec !== null &&
    (spec as BarChartSpec).type === 'bar' &&
    Array.isArray((spec as BarChartSpec).data)
  )
}

function fillForValue(
  v: number | undefined,
  vmin: number,
  vmax: number,
): string {
  if (v === undefined || v <= 0) return 'var(--origins-map-empty, #e8eaed)'
  if (vmax <= vmin) return `rgba(${R},${G},${B},0.78)`
  const t = (v - vmin) / (vmax - vmin)
  const a = 0.14 + t * 0.78
  return `rgba(${R},${G},${B},${a})`
}

type UsRow = { name: string; value: number }

export function OriginsMaps({ bundle }: { bundle: TabBundle }) {
  const [tip, setTip] = useState<{
    title: string
    value: number | undefined
    x: number
    y: number
  } | null>(null)

  const usSpec = bundle.charts.us_states
  const countriesSpec = bundle.charts.countries

  const statesFc = useMemo(() => {
    const topo = usStatesTopology as unknown as Topology
    return feature(
      topo,
      topo.objects.states as GeometryCollection,
    ) as FeatureCollection<Geometry & { name?: string }>
  }, [])

  const countriesFc = useMemo(() => {
    const topo = countriesTopology as unknown as Topology
    return feature(
      topo,
      topo.objects.countries as GeometryCollection,
    ) as FeatureCollection<Geometry & { name?: string }>
  }, [])

  const topoCountryNames = useMemo(() => {
    return buildTopoNameSet(
      countriesFc.features.map((f) => String(f.properties?.name ?? '')),
    )
  }, [countriesFc])

  const usRows: UsRow[] = useMemo(() => {
    if (!isBarChart(usSpec)) return []
    return usSpec.data.map((d) => ({ name: d.label, value: d.value }))
  }, [usSpec])

  const valueByStateName = useMemo(() => {
    const m = new Map<string, number>()
    for (const r of usRows) {
      const k = r.name.trim()
      m.set(k, (m.get(k) ?? 0) + r.value)
    }
    return m
  }, [usRows])

  const usValues = useMemo(
    () => [...valueByStateName.values()].filter((v) => v > 0),
    [valueByStateName],
  )
  const usMin = usValues.length ? Math.min(...usValues) : 0
  const usMax = usValues.length ? Math.max(...usValues) : 1

  const worldPlan = useMemo(() => {
    if (!isBarChart(countriesSpec)) return null
    const rows = countriesSpec.data
    if (rows.length === 0) return null

    const single = rows.length === 1
    const only = rows[0]
    if (single && isUnmappedCountryBucket(only.label)) {
      return {
        mode: 'intl_aggregate' as const,
        aggregate: only.value,
        unmappedNote: only.label,
      }
    }

    const byTopo = new Map<string, number>()
    const unmapped: { label: string; value: number }[] = []
    for (const r of rows) {
      if (isUnmappedCountryBucket(r.label)) {
        unmapped.push({ label: r.label, value: r.value })
        continue
      }
      const topo = labelToTopoCountryName(r.label, topoCountryNames)
      if (topo) {
        byTopo.set(topo, (byTopo.get(topo) ?? 0) + r.value)
      } else {
        unmapped.push({ label: r.label, value: r.value })
      }
    }
    const vals = [...byTopo.values()]
    const wMin = vals.length ? Math.min(...vals) : 0
    const wMax = vals.length ? Math.max(...vals) : 1
    return {
      mode: 'per_country' as const,
      byTopo,
      wMin,
      wMax,
      unmapped,
    }
  }, [countriesSpec, topoCountryNames])

  const usPath = useMemo(() => {
    const proj = geoAlbersUsa()
    proj.fitSize([US_W, US_H], statesFc as GeoJSON)
    return geoPath(proj)
  }, [statesFc])

  const worldPath = useMemo(() => {
    const proj = geoNaturalEarth1()
    proj.fitSize([WORLD_W, WORLD_H], countriesFc as GeoJSON)
    return geoPath(proj)
  }, [countriesFc])

  if (!isBarChart(usSpec) && !isBarChart(countriesSpec)) return null

  const showUs = isBarChart(usSpec) && usRows.length > 0
  const showWorld = worldPlan !== null

  if (!showUs && !showWorld) return null

  return (
    <section className="origins-maps" aria-label="Origin maps">
      {tip && (
        <div
          className="origins-map-tooltip"
          style={{ left: tip.x, top: tip.y }}
          role="tooltip"
        >
          <strong>{tip.title}</strong>
          <span>
            {tip.value !== undefined
              ? tip.value.toLocaleString()
              : '—'}{' '}
            students
          </span>
        </div>
      )}

      <div className="origins-maps-grid">
        {showUs && (
          <div className="origins-map-panel">
            <h3 className="origins-map-title">United States — by home state</h3>
            <p className="origins-map-sub muted small">
              Darker red = more students (same data as the bar chart below).
            </p>
            <svg
              className="origins-map-svg"
              viewBox={`0 0 ${US_W} ${US_H}`}
              aria-label="Choropleth map of US states"
            >
              {statesFc.features.map((f, i) => {
                const name = String(f.properties?.name ?? '')
                const v = valueByStateName.get(name)
                const d = usPath(f)
                if (!d) return null
                return (
                  <path
                    key={f.id ?? `us-${i}`}
                    d={d}
                    fill={fillForValue(v, usMin, usMax)}
                    stroke="var(--border, #ccc)"
                    strokeWidth={0.35}
                    vectorEffect="non-scaling-stroke"
                    className="origins-map-path"
                    onMouseEnter={(ev) => {
                      setTip({
                        title: name,
                        value: v,
                        x: ev.clientX + 12,
                        y: ev.clientY + 12,
                      })
                    }}
                    onMouseMove={(ev) => {
                      setTip((t) =>
                        t
                          ? {
                              ...t,
                              x: ev.clientX + 12,
                              y: ev.clientY + 12,
                            }
                          : null,
                      )
                    }}
                    onMouseLeave={() => setTip(null)}
                  />
                )
              })}
            </svg>
            <div className="origins-map-legend" aria-hidden>
              <span className="muted small">Fewer</span>
              <div className="origins-map-legend-bar" />
              <span className="muted small">More</span>
            </div>
          </div>
        )}

        {showWorld && worldPlan && (
          <div className="origins-map-panel">
            <h3 className="origins-map-title">World — by country of origin</h3>
            <p className="origins-map-sub muted small">
              {worldPlan.mode === 'intl_aggregate'
                ? 'IPEDS reports one international bucket; all non-U.S. countries share the same shade (not a geographic split).'
                : 'Darker red = more students. “Other” buckets are listed below the map when present.'}
            </p>
            <svg
              className="origins-map-svg"
              viewBox={`0 0 ${WORLD_W} ${WORLD_H}`}
              aria-label="Choropleth map of countries"
            >
              {countriesFc.features.map((f, i) => {
                const name = String(f.properties?.name ?? '')
                const d = worldPath(f)
                if (!d) return null
                let v: number | undefined
                let wmin = 0
                let wmax = 1
                if (worldPlan.mode === 'intl_aggregate') {
                  wmin = 0
                  wmax = Math.max(worldPlan.aggregate, 1)
                  v =
                    name === 'United States of America'
                      ? undefined
                      : worldPlan.aggregate
                } else {
                  wmin = worldPlan.wMin
                  wmax = worldPlan.wMax
                  v = worldPlan.byTopo.get(name)
                }
                return (
                  <path
                    key={f.id ?? `w-${i}`}
                    d={d}
                    fill={fillForValue(v, wmin, wmax)}
                    stroke="var(--border, #ccc)"
                    strokeWidth={0.2}
                    vectorEffect="non-scaling-stroke"
                    className="origins-map-path"
                    onMouseEnter={(ev) => {
                      setTip({
                        title: name,
                        value: v,
                        x: ev.clientX + 12,
                        y: ev.clientY + 12,
                      })
                    }}
                    onMouseMove={(ev) => {
                      setTip((t) =>
                        t
                          ? {
                              ...t,
                              x: ev.clientX + 12,
                              y: ev.clientY + 12,
                            }
                          : null,
                      )
                    }}
                    onMouseLeave={() => setTip(null)}
                  />
                )
              })}
            </svg>
            <div className="origins-map-legend" aria-hidden>
              <span className="muted small">Fewer</span>
              <div className="origins-map-legend-bar" />
              <span className="muted small">More</span>
            </div>
            {worldPlan.mode === 'per_country' &&
              worldPlan.unmapped.length > 0 && (
                <p className="origins-map-footnote muted small">
                  Not shown on map:{' '}
                  {worldPlan.unmapped
                    .map((u) => `${u.label} (${u.value.toLocaleString()})`)
                    .join(' · ')}
                </p>
              )}
          </div>
        )}
      </div>
    </section>
  )
}
