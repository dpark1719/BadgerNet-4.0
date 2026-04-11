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

const ARENA_W = 880
const ARENA_H = 480
const R_MIN = 26
const R_MAX = 72

type SimBubble = VizualiveNode &
  SimulationNodeDatum & {
    radius: number
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

export default function VizualivePanel() {
  const clipId = useId().replace(/[^a-zA-Z0-9]/g, '')
  const clipPathId = `viz-clip-${clipId}`

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
    if (currentNodes.length === 0) {
      return undefined
    }

    const simNodes: SimBubble[] = currentNodes.map((n) => ({
      ...n,
      radius: bubbleRadius(n.count, maxCount),
    }))

    const cx = ARENA_W / 2
    const cy = ARENA_H / 2
    simNodes.forEach((n, i) => {
      const angle = (i / simNodes.length) * Math.PI * 2
      const r = Math.min(ARENA_W, ARENA_H) * 0.22
      n.x = cx + Math.cos(angle) * r
      n.y = cy + Math.sin(angle) * r
    })

    const sim = forceSimulation(simNodes)
      .force(
        'charge',
        forceManyBody<SimBubble>().strength((d) => -28 * Math.sqrt(d.radius)),
      )
      .force(
        'collide',
        forceCollide<SimBubble>()
          .radius((d) => d.radius + 6)
          .strength(0.85)
          .iterations(2),
      )
      .force('center', forceCenter(cx, cy))
      .alphaDecay(0.022)
      .velocityDecay(0.31)

    sim.on('tick', () => {
      simNodes.forEach((n) => {
        if (n.x !== undefined) {
          n.x = Math.max(n.radius, Math.min(ARENA_W - n.radius, n.x))
        }
        if (n.y !== undefined) {
          n.y = Math.max(n.radius, Math.min(ARENA_H - n.radius, n.y))
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

  const goBack = () => {
    setPath((p) => p.slice(0, -1))
  }

  const goToIndex = (index: number) => {
    setPath((p) => p.slice(0, index + 1))
  }

  const resetRoot = () => {
    setPath([])
  }

  const hovered = bubbles.find((b) => b.id === hoverId)

  if (bundle.status === 'loading') {
    return <p className="muted">Loading Vizualive…</p>
  }
  if (bundle.status === 'err') {
    return (
      <p className="banner error" role="alert">
        {bundle.message}
      </p>
    )
  }

  return (
    <div className="vizualive">
      <section className="meta-strip viz-intro" aria-label="Data context">
        <p className="methodology">{bundle.data.meta.methodology}</p>
        {bundle.data.meta.disclaimer && (
          <p className="disclaimer">{bundle.data.meta.disclaimer}</p>
        )}
      </section>

      <div className="viz-toolbar">
        <nav className="viz-breadcrumb" aria-label="Drill path">
          <button type="button" className="viz-crumb" onClick={resetRoot}>
            Roots
          </button>
          {path.map((node, i) => (
            <span key={node.id} className="viz-crumb-wrap">
              <span className="viz-crumb-sep" aria-hidden>
                /
              </span>
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
          <button
            type="button"
            className="tab"
            disabled={path.length === 0}
            onClick={goBack}
          >
            Back
          </button>
        </div>
      </div>

      <p className="muted small viz-hint">
        Bubble size reflects headcount (sqrt scale). Click a bubble to drill
        when it has a next level. Drag simulation settles automatically.
      </p>

      <div className="viz-arena-wrap">
        <svg
          className="viz-arena"
          viewBox={`0 0 ${ARENA_W} ${ARENA_H}`}
          width="100%"
          height="auto"
          role="application"
          aria-label="Vizualive bubble arena"
        >
          <defs>
            <clipPath id={clipPathId}>
              <rect
                x={4}
                y={4}
                width={ARENA_W - 8}
                height={ARENA_H - 8}
                rx={20}
                ry={20}
              />
            </clipPath>
          </defs>
          <rect
            className="viz-arena-bg"
            x={0}
            y={0}
            width={ARENA_W}
            height={ARENA_H}
            rx={22}
          />
          <g clipPath={`url(#${clipPathId})`}>
            {bubbles.map((b) => {
              const x = b.x ?? ARENA_W / 2
              const y = b.y ?? ARENA_H / 2
              const canDrill = Boolean(b.children?.length)
              return (
                <g
                  key={b.id}
                  className={`viz-bubble-group${canDrill ? ' viz-bubble-group--drill' : ''}`}
                  transform={`translate(${x},${y})`}
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
                  aria-label={`${b.label}, count ${b.count}${canDrill ? ', press to open subgroup' : ', leaf'}`}
                >
                  <circle
                    className="viz-bubble-fill"
                    r={b.radius}
                    style={{
                      opacity: canDrill ? 0.92 : 0.72,
                    }}
                  />
                  <text className="viz-bubble-label" textAnchor="middle" dy="-0.15em">
                    {b.label.length > 18 ? `${b.label.slice(0, 16)}…` : b.label}
                  </text>
                  <text
                    className="viz-bubble-count"
                    textAnchor="middle"
                    dy="1.05em"
                  >
                    {b.count}
                  </text>
                </g>
              )
            })}
          </g>
        </svg>

        {hovered?.subtitle && (
          <div className="viz-tooltip" role="status">
            <strong>{hovered.label}</strong>
            <p className="viz-tooltip-sub">{hovered.subtitle}</p>
            <p className="viz-tooltip-count muted small">Count: {hovered.count}</p>
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
              <span className="muted small"> — {n.count}</span>
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
