import { useEffect, useMemo, useRef, useState } from 'react'
import { geoOrthographic, geoPath, geoGraticule } from 'd3-geo'
import { feature } from 'topojson-client'
import type { FeatureCollection, Feature } from 'geojson'
import type { GeometryCollection, Topology } from 'topojson-specification'
import countriesTopology from 'world-atlas/countries-110m.json'
import './LandingPage.css'

const MADISON: [number, number] = [-89.4012, 43.0731]
const GLOBE_SIZE = 600

/** D3 orthographic `.rotate([a, b])` centers the point at geographic (-a, -b). */
function orthographicRotateToCenter(lon: number, lat: number): [number, number] {
  return [-lon, -lat]
}

const SCROLL_STEPS = 6

interface Props {
  onEnter: () => void
}

export default function LandingPage({ onEnter }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    const el = containerRef.current
    if (!el) return
    const onScroll = () => {
      const scrollTop = el.scrollTop
      const maxScroll = el.scrollHeight - el.clientHeight
      if (maxScroll <= 0) {
        setProgress(0)
        return
      }
      setProgress(Math.min(1, scrollTop / maxScroll))
    }
    el.addEventListener('scroll', onScroll, { passive: true })
    return () => el.removeEventListener('scroll', onScroll)
  }, [])

  const countriesFc = useMemo(() => {
    const topo = countriesTopology as unknown as Topology
    return feature(
      topo,
      topo.objects.countries as GeometryCollection,
    ) as FeatureCollection
  }, [])

  const graticule = useMemo(() => geoGraticule().step([15, 15])(), [])

  const scale = 120 + progress * 2800
  const [rotEndLon, rotEndLat] = orthographicRotateToCenter(MADISON[0], MADISON[1])
  // Start with the Western Hemisphere facing forward, then pan/zoom to Madison.
  const [rotStartLon, rotStartLat] = orthographicRotateToCenter(-75, 28)
  const rotateLon = rotStartLon + progress * (rotEndLon - rotStartLon)
  const rotateLat = rotStartLat + progress * (rotEndLat - rotStartLat)

  const projection = useMemo(() => {
    return geoOrthographic()
      .scale(scale)
      .translate([GLOBE_SIZE / 2, GLOBE_SIZE / 2])
      .rotate([rotateLon, rotateLat, 0])
      .clipAngle(90)
  }, [scale, rotateLon, rotateLat])

  const pathGen = useMemo(() => geoPath(projection), [projection])

  const madisonXY = projection(MADISON)

  const textOpacity = Math.max(0, 1 - progress * 3)
  const subtitleOpacity = Math.max(0, Math.min(1, (progress - 0.15) * 4))
  const madisonLabelOpacity = Math.max(0, Math.min(1, (progress - 0.5) * 3))
  const ctaOpacity = Math.max(0, Math.min(1, (progress - 0.75) * 4))
  const globeOpacity = 0.15 + progress * 0.85

  return (
    <div className="landing" ref={containerRef}>
      <div className="landing-scroll-spacer" style={{ height: `${SCROLL_STEPS * 100}vh` }}>
        <div className="landing-sticky">
          <div className="landing-globe-container" style={{ opacity: globeOpacity }}>
            <svg
              className="landing-globe"
              viewBox={`0 0 ${GLOBE_SIZE} ${GLOBE_SIZE}`}
              width="100%"
              height="100%"
            >
              <defs>
                <radialGradient id="globe-ocean" cx="40%" cy="35%" r="60%">
                  <stop offset="0%" stopColor="rgba(4,121,168,0.12)" />
                  <stop offset="100%" stopColor="rgba(4,121,168,0.03)" />
                </radialGradient>
                <radialGradient id="globe-shine" cx="35%" cy="30%" r="65%">
                  <stop offset="0%" stopColor="rgba(255,255,255,0.18)" />
                  <stop offset="60%" stopColor="rgba(255,255,255,0)" />
                </radialGradient>
                <filter id="globe-shadow" x="-20%" y="-20%" width="140%" height="140%">
                  <feDropShadow dx="0" dy="8" stdDeviation="20" floodColor="rgba(0,0,0,0.15)" />
                </filter>
              </defs>

              <circle
                cx={GLOBE_SIZE / 2}
                cy={GLOBE_SIZE / 2}
                r={scale < GLOBE_SIZE / 2 ? scale : GLOBE_SIZE / 2 - 2}
                fill="url(#globe-ocean)"
                stroke="rgba(197,5,12,0.15)"
                strokeWidth={1}
                filter="url(#globe-shadow)"
              />

              <path
                d={pathGen(graticule) ?? ''}
                fill="none"
                stroke="rgba(197,5,12,0.06)"
                strokeWidth={0.5}
              />

              <g>
                {countriesFc.features.map((f) => {
                  const name = (f.properties as { name?: string })?.name ?? ''
                  const d = pathGen(f as Feature) ?? ''
                  return (
                    <path
                      key={String(f.id ?? name ?? d.slice(0, 20))}
                      d={d}
                      className="landing-country"
                    />
                  )
                })}
              </g>

              <circle
                cx={GLOBE_SIZE / 2}
                cy={GLOBE_SIZE / 2}
                r={scale < GLOBE_SIZE / 2 ? scale : GLOBE_SIZE / 2 - 2}
                fill="url(#globe-shine)"
                style={{ pointerEvents: 'none' }}
              />

              {madisonXY && (
                <g style={{ opacity: madisonLabelOpacity, transition: 'opacity 0.3s' }}>
                  <circle
                    cx={madisonXY[0]}
                    cy={madisonXY[1]}
                    r={Math.max(3, 2 + progress * 10)}
                    fill="#c5050c"
                    stroke="#fff"
                    strokeWidth={2}
                  />
                  <circle
                    cx={madisonXY[0]}
                    cy={madisonXY[1]}
                    r={Math.max(8, 6 + progress * 18)}
                    fill="none"
                    stroke="rgba(197,5,12,0.4)"
                    strokeWidth={1.5}
                    className="landing-pulse"
                  />
                  {progress > 0.5 && (
                    <text
                      x={madisonXY[0] + 12 + progress * 5}
                      y={madisonXY[1] - 8 - progress * 5}
                      className="landing-madison-label"
                    >
                      Madison, WI
                    </text>
                  )}
                </g>
              )}
            </svg>
          </div>

          <div className="landing-overlay">
            <div className="landing-text-block" style={{ opacity: textOpacity }}>
              <p className="landing-welcome">Welcome to the</p>
              <h1 className="landing-title">
                University of<br />Wisconsin–Madison
              </h1>
            </div>

            <div className="landing-subtitle-block" style={{ opacity: subtitleOpacity }}>
              <p className="landing-subtitle">
                Where do Badgers go after graduation?
              </p>
              <p className="landing-subtitle-small">
                Explore alumni outcomes across the globe
              </p>
            </div>

            <div className="landing-cta-block" style={{ opacity: ctaOpacity }}>
              <div className="landing-glass-card">
                <h2 className="landing-card-title">BadgerNet 4.0</h2>
                <p className="landing-card-desc">
                  Interactive data-driven exploration of post-graduation outcomes
                </p>
                <button
                  type="button"
                  className="landing-enter-btn"
                  onClick={onEnter}
                >
                  Explore the data
                </button>
              </div>
            </div>
          </div>

          <div className="landing-scroll-hint" style={{ opacity: progress < 0.1 ? 1 : 0 }}>
            <span className="landing-scroll-arrow">↓</span>
            <span>Scroll to zoom into Madison</span>
          </div>
        </div>
      </div>
    </div>
  )
}
