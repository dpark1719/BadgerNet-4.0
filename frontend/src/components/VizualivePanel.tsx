import {
  useCallback,
  useEffect,
  useId,
  useMemo,
  useState,
} from 'react'
import {
  forceCenter,
  forceCollide,
  forceManyBody,
  forceSimulation,
} from 'd3-force'
import type { SimulationNodeDatum } from 'd3-force'
import { publicPath } from '../publicPath'
import type { VizualiveBundle, VizualiveNode } from '../types/vizualive'
import './VizualivePanel.css'

const ARENA_W = 920
const ARENA_H = 520
const R_MIN = 34
const R_MAX = 100

type SimBubble = VizualiveNode &
  SimulationNodeDatum & {
    radius: number
    idx: number
  }

async function loadJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

function bubbleRadius(count: number, maxCount: number): number {
  if (maxCount <= 0) return (R_MIN + R_MAX) / 2
  const t = Math.sqrt(count / maxCount)
  return R_MIN + (R_MAX - R_MIN) * t
}

function truncateLabel(label: string, radius: number): string {
  const maxChars = Math.max(4, Math.floor(radius / 5))
  if (label.length <= maxChars) return label
  return label.slice(0, maxChars - 1) + '…'
}

export default function VisualizePanel() {
  const clipId = useId().replace(/[^a-zA-Z0-9]/g, '')
  const clipPathId = `viz-clip-${clipId}`
  const glassPrefix = `viz-glass-${clipId}`

  const [bundle, setBundle] = useState<
    | { status: 'loading' }
    | { status: 'ok'; data: VizualiveBundle }
    | { status: 'err'; message: string }
  >({ status: 'loading' })

  const [path, setPath] = useState<VizualiveNode[]>([])
  const [bubbles, setBubbles] = useState<SimBubble[]>([])
  const [hoverId, setHoverId] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    loadJson<VizualiveBundle>(publicPath('data/vizualive.json'))
      .then((data) => {
        if (!cancelled) setBundle({ status: 'ok', data })
      })
      .catch((e: Error) => {
        if (!cancelled) setBundle({ status: 'err', message: e.message })
      })
    return () => {
      cancelled = true
    }
  }, [])

  const currentNodes = useMemo(() => {
    if (bundle.status !== 'ok') return []
    const roots = bundle.data.roots
    if (path.length === 0) return roots
    const last = path[path.length - 1]
    return last.children ?? []
  }, [bundle, path])

  const maxCount = useMemo(
    () =>
      currentNodes.length
        ? Math.max(...currentNodes.map((n) => n.count), 1)
        : 1,
    [currentNodes],
  )

  const levelKey = useMemo(
    () => currentNodes.map((n) => `${n.id}:${n.count}`).join('|'),
    [currentNodes],
  )

  const restartSimulation = useCallback((): (() => void) | undefined => {
    if (currentNodes.length === 0) return undefined

    const simNodes: SimBubble[] = currentNodes.map((n, i) => ({
      ...n,
      radius: bubbleRadius(n.count, maxCount),
      idx: i,
    }))

    const cx = ARENA_W / 2
    const cy = ARENA_H / 2
    simNodes.forEach((n, i) => {
      const angle = (i / simNodes.length) * Math.PI * 2
      const r = Math.min(ARENA_W, ARENA_H) * 0.18
      n.x = cx + Math.cos(angle) * r
      n.y = cy + Math.sin(angle) * r
    })

    const sim = forceSimulation(simNodes)
      .force(
        'charge',
        forceManyBody<SimBubble>().strength((d) => -18 * Math.sqrt(d.radius)),
      )
      .force(
        'collide',
        forceCollide<SimBubble>()
          .radius((d) => d.radius + 10)
          .strength(0.9)
          .iterations(3),
      )
      .force('center', forceCenter(cx, cy).strength(0.8))
      .alphaDecay(0.02)
      .velocityDecay(0.35)

    sim.on('tick', () => {
      simNodes.forEach((n) => {
        if (n.x !== undefined) {
          n.x = Math.max(n.radius + 6, Math.min(ARENA_W - n.radius - 6, n.x))
        }
        if (n.y !== undefined) {
          n.y = Math.max(n.radius + 6, Math.min(ARENA_H - n.radius - 6, n.y))
        }
      })
      setBubbles(simNodes.map((n) => ({ ...n })))
    })

    sim.alpha(1).restart()

    return () => {
      sim.stop()
      sim.on('tick', null)
    }
  }, [currentNodes, maxCount])

  useEffect(() => {
    let cleanup: (() => void) | undefined
    const timer = window.setTimeout(() => {
      if (currentNodes.length === 0) {
        setBubbles([])
      } else {
        cleanup = restartSimulation()
      }
    }, 0)
    return () => {
      window.clearTimeout(timer)
      cleanup?.()
    }
  }, [levelKey, currentNodes.length, restartSimulation])

  const drill = (node: VizualiveNode) => {
    if (node.children?.length) {
      setPath((p) => [...p, node])
    }
  }

  const goBack = () => setPath((p) => p.slice(0, -1))
  const goToIndex = (index: number) => setPath((p) => p.slice(0, index + 1))
  const resetRoot = () => setPath([])

  const hovered = bubbles.find((b) => b.id === hoverId)

  if (bundle.status === 'loading') {
    return <p className="muted">Loading Visualize…</p>
  }
  if (bundle.status === 'err') {
    return (
      <p className="banner error" role="alert">
        {bundle.message}
      </p>
    )
  }

  return (
    <div className="visualize">
      <section className="meta-strip viz-intro" aria-label="Data context">
        <p className="methodology">{bundle.data.meta.methodology}</p>
        {bundle.data.meta.disclaimer && (
          <p className="disclaimer">{bundle.data.meta.disclaimer}</p>
        )}
      </section>

      <div className="viz-toolbar">
        <nav className="viz-breadcrumb" aria-label="Drill path">
          <button type="button" className="viz-crumb viz-crumb--root" onClick={resetRoot}>
            All paths
          </button>
          {path.map((node, i) => (
            <span key={node.id} className="viz-crumb-wrap">
              <span className="viz-crumb-sep" aria-hidden>›</span>
              <button
                type="button"
                className="viz-crumb"
                onClick={() => goToIndex(i)}
              >
                {node.label}
              </button>
            </span>
          ))}
        </nav>
        <div className="viz-toolbar-actions">
          {path.length > 0 && (
            <button type="button" className="viz-back-btn" onClick={goBack}>
              ← Back
            </button>
          )}
        </div>
      </div>

      <p className="muted small viz-hint">
        Click a bubble to drill down into sub-categories. Bubble size = headcount.
      </p>

      <div className="viz-arena-wrap">
        <svg
          className="viz-arena"
          viewBox={`0 0 ${ARENA_W} ${ARENA_H}`}
          width="100%"
          height="auto"
          role="application"
          aria-label="Visualize bubble arena"
        >
          <defs>
            <clipPath id={clipPathId}>
              <rect
                x={4}
                y={4}
                width={ARENA_W - 8}
                height={ARENA_H - 8}
                rx={24}
                ry={24}
              />
            </clipPath>
            <radialGradient id={`${glassPrefix}-bg`} cx="30%" cy="25%" r="70%">
              <stop offset="0%" stopColor="rgba(255,255,255,0.55)" />
              <stop offset="100%" stopColor="rgba(255,255,255,0.15)" />
            </radialGradient>
            <radialGradient id={`${glassPrefix}-shine`} cx="38%" cy="28%" r="55%">
              <stop offset="0%" stopColor="rgba(255,255,255,0.7)" />
              <stop offset="50%" stopColor="rgba(255,255,255,0.15)" />
              <stop offset="100%" stopColor="rgba(255,255,255,0)" />
            </radialGradient>
            <filter id={`${glassPrefix}-blur`} x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur in="SourceAlpha" stdDeviation="3" result="shadow" />
              <feOffset dy="2" result="offsetShadow" />
              <feFlood floodColor="rgba(0,0,0,0.08)" />
              <feComposite in2="offsetShadow" operator="in" />
              <feMerge>
                <feMergeNode />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>
          <rect
            className="viz-arena-bg"
            x={0}
            y={0}
            width={ARENA_W}
            height={ARENA_H}
            rx={24}
          />
          <g clipPath={`url(#${clipPathId})`}>
            {bubbles.map((b) => {
              const x = b.x ?? ARENA_W / 2
              const y = b.y ?? ARENA_H / 2
              const canDrill = Boolean(b.children?.length)
              const isHovered = hoverId === b.id
              const s = isHovered ? 1.06 : 1
              const showHint = canDrill && b.radius > 44
              return (
                <g
                  key={b.id}
                  className={`viz-bubble-group${canDrill ? ' viz-bubble-group--drill' : ''}`}
                  transform={`translate(${x},${y}) scale(${s})`}
                  onMouseEnter={() => setHoverId(b.id)}
                  onMouseLeave={() => setHoverId(null)}
                  onClick={() => drill(b)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      drill(b)
                    }
                  }}
                  role={canDrill ? 'button' : undefined}
                  tabIndex={canDrill ? 0 : -1}
                  aria-label={`${b.label}, count ${b.count}${canDrill ? ', click to expand' : ''}`}
                  filter={`url(#${glassPrefix}-blur)`}
                  style={{ transition: 'transform 0.2s ease-out' }}
                >
                  {/* Glass body */}
                  <circle
                    r={b.radius}
                    fill={`url(#${glassPrefix}-bg)`}
                    stroke="rgba(255,255,255,0.6)"
                    strokeWidth={1.5}
                    className="viz-glass-body"
                  />
                  {/* Inner accent ring */}
                  <circle
                    r={b.radius - 3}
                    fill="none"
                    stroke="rgba(197,5,12,0.12)"
                    strokeWidth={1}
                  />
                  {/* Shine highlight */}
                  <ellipse
                    cx={-b.radius * 0.15}
                    cy={-b.radius * 0.2}
                    rx={b.radius * 0.55}
                    ry={b.radius * 0.35}
                    fill={`url(#${glassPrefix}-shine)`}
                    style={{ pointerEvents: 'none' }}
                  />
                  {/* Label */}
                  <text
                    className="viz-bubble-label"
                    textAnchor="middle"
                    dy={showHint ? '-0.6em' : '-0.15em'}
                  >
                    {truncateLabel(b.label, b.radius)}
                  </text>
                  {/* Count */}
                  <text
                    className="viz-bubble-count"
                    textAnchor="middle"
                    dy={showHint ? '0.7em' : '1.0em'}
                  >
                    {b.count.toLocaleString()}
                  </text>
                  {/* Drill hint — only on big enough bubbles */}
                  {showHint && (
                    <text
                      className="viz-bubble-drill-hint"
                      textAnchor="middle"
                      dy="1.9em"
                    >
                      click to explore ›
                    </text>
                  )}
                </g>
              )
            })}
          </g>
        </svg>

        {hovered && (
          <div className="viz-tooltip" role="status">
            <strong>{hovered.label}</strong>
            <p className="viz-tooltip-count">
              {hovered.count.toLocaleString()} alumni
            </p>
            {hovered.subtitle && (
              <p className="viz-tooltip-sub">{hovered.subtitle}</p>
            )}
            {hovered.children?.length ? (
              <p className="viz-tooltip-drill">Click to see {hovered.children.length} sub-categories</p>
            ) : (
              <p className="viz-tooltip-drill viz-tooltip-leaf">Leaf category</p>
            )}
          </div>
        )}
      </div>

      <details className="viz-a11y">
        <summary>Outline view (keyboard / screen reader)</summary>
        <ul className="viz-a11y-list">
          {currentNodes.map((n) => (
            <li key={n.id}>
              <button
                type="button"
                className="link-button"
                onClick={() => drill(n)}
                disabled={!n.children?.length}
              >
                {n.label}
              </button>
              <span className="muted small"> — {n.count.toLocaleString()}</span>
              {n.subtitle && (
                <span className="muted small"> ({n.subtitle})</span>
              )}
            </li>
          ))}
        </ul>
      </details>
    </div>
  )
}
