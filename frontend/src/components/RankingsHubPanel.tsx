import { useMemo, useState } from 'react'
import type { InstitutionRankRow, MajorRankingsBundle, RankingsHubBundle } from '../types/data'
import { MajorRankingsPanel } from './MajorRankingsPanel'
import './RankingsHubPanel.css'

type SubKey = 'global' | 'us' | 'public' | 'majors'

const STEP = 5
const INITIAL_SPAN = 5

function isInstitutionSub(sub: SubKey): sub is Exclude<SubKey, 'majors'> {
  return sub !== 'majors'
}

const SUBS: { id: SubKey; label: string }[] = [
  { id: 'global', label: 'World peers' },
  { id: 'us', label: 'U.S. only' },
  { id: 'public', label: 'Public only' },
  { id: 'majors', label: 'UW programs' },
]

function fmtRank(n: number | null | undefined) {
  if (n == null) return '—'
  return String(n)
}

function sortByMetric(rows: InstitutionRankRow[], metric: 'qs_rank' | 'arwu_rank'): InstitutionRankRow[] {
  return [...rows].sort((a, b) => {
    const ar = a[metric]
    const br = b[metric]
    const aNull = ar == null
    const bNull = br == null
    if (aNull !== bNull) return aNull ? 1 : -1
    if (!aNull && !bNull && ar !== br) return (ar as number) - (br as number)
    return a.label.localeCompare(b.label)
  })
}

function anchorIndex(rows: InstitutionRankRow[]): number {
  const byFlag = rows.findIndex((r) => r.anchor)
  if (byFlag >= 0) return byFlag
  return rows.findIndex((r) => /UW/i.test(r.label) && /Madison/i.test(r.label))
}

function NeighborhoodBlock({
  rows,
  metric,
  title,
  note,
}: {
  rows: InstitutionRankRow[]
  metric: 'qs_rank' | 'arwu_rank'
  title: string
  note: string
}) {
  const [aboveN, setAboveN] = useState(INITIAL_SPAN)
  const [belowN, setBelowN] = useState(INITIAL_SPAN)

  const anchorRow = useMemo(() => {
    const a = rows.find((r) => r.anchor)
    if (a) return a
    return rows.find((r) => /UW/i.test(r.label) && /Madison/i.test(r.label))
  }, [rows])

  const anchorHasMetric = anchorRow != null && anchorRow[metric] != null

  const ranked = useMemo(() => rows.filter((r) => r[metric] != null), [rows, metric])
  const sortedRanked = useMemo(() => sortByMetric(ranked, metric), [ranked, metric])
  const idx = useMemo(() => anchorIndex(sortedRanked), [sortedRanked])

  const unrankedLabels = useMemo(() => {
    const missing = rows.filter((r) => r[metric] == null).map((r) => r.label)
    return missing
  }, [rows, metric])

  const maxAbove = idx >= 0 ? idx : 0
  const maxBelow = idx >= 0 ? sortedRanked.length - 1 - idx : 0

  const effAbove = idx >= 0 ? Math.min(aboveN, maxAbove) : 0
  const effBelow = idx >= 0 ? Math.min(belowN, maxBelow) : 0

  const windowRows =
    idx >= 0 ? sortedRanked.slice(idx - effAbove, idx + effBelow + 1) : sortedRanked

  const canMoreAbove = idx >= 0 && effAbove < maxAbove
  const canMoreBelow = idx >= 0 && effBelow < maxBelow

  const metricLabel = metric === 'qs_rank' ? 'QS world' : 'ARWU'

  if (anchorRow && !anchorHasMetric) {
    return (
      <section className="rankings-neighborhood" aria-labelledby={`${metric}-missing-title`}>
        <h3 className="rankings-neighborhood-title" id={`${metric}-missing-title`}>
          {title}
        </h3>
        <p className="rankings-neighborhood-note muted small">
          UW–Madison has no {metricLabel} rank in this Wikidata snapshot, so a neighborhood slice is
          not available. The full peer list is shown sorted by {metricLabel} (schools without a
          rank appear last).
        </p>
        <InstitutionTable rows={sortByMetric(rows, metric)} />
      </section>
    )
  }

  if (idx < 0) {
    return (
      <section className="rankings-neighborhood" aria-labelledby={`${metric}-fallback-title`}>
        <h3 className="rankings-neighborhood-title" id={`${metric}-fallback-title`}>
          {title}
        </h3>
        <p className="rankings-neighborhood-note muted small">
          UW–Madison is not in this filtered list, so the full peer set is shown sorted by this
          ranking (unranked schools last).
        </p>
        <InstitutionTable rows={sortByMetric(rows, metric)} />
      </section>
    )
  }

  if (sortedRanked.length === 0) {
    return (
      <section className="rankings-neighborhood">
        <h3 className="rankings-neighborhood-title">{title}</h3>
        <p className="rankings-neighborhood-note muted small">No schools in this tab have a value for this ranking.</p>
      </section>
    )
  }

  return (
    <section className="rankings-neighborhood" aria-labelledby={`${metric}-title`}>
      <h3 className="rankings-neighborhood-title" id={`${metric}-title`}>
        {title}
      </h3>
      <p className="rankings-neighborhood-note muted small">{note}</p>

      <div className="rankings-expand-bar">
        <button
          type="button"
          className="rankings-expand-btn"
          disabled={!canMoreAbove}
          onClick={() => setAboveN((n) => Math.min(n + STEP, maxAbove))}
        >
          Show {STEP} more above (better ranks)
        </button>
        <span className="rankings-expand-hint muted small">
          {idx >= 0
            ? `Showing ${effAbove} better · UW–Madison · ${effBelow} worse (within peers with a ${metric === 'qs_rank' ? 'QS' : 'ARWU'} rank).`
            : null}
        </span>
      </div>

      <div className="rankings-table-wrap">
        <table className="rankings-inst-table">
          <thead>
            <tr>
              <th scope="col">Institution</th>
              <th scope="col">Region</th>
              <th scope="col" className="num">
                QS world
              </th>
              <th scope="col" className="num">
                QS yr
              </th>
              <th scope="col" className="num">
                ARWU
              </th>
              <th scope="col" className="num">
                ARWU yr
              </th>
            </tr>
          </thead>
          <tbody>
            {windowRows.map((r, i) => (
              <tr key={`${r.label}-${metric}-${i}`} className={r.anchor ? 'rankings-anchor-row' : undefined}>
                <td>{r.label}</td>
                <td>{r.country || '—'}</td>
                <td className="num">{fmtRank(r.qs_rank)}</td>
                <td className="num">{r.qs_year ?? '—'}</td>
                <td className="num">{fmtRank(r.arwu_rank)}</td>
                <td className="num">{r.arwu_year ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="muted small rankings-table-note">
          Lower {metric === 'qs_rank' ? 'QS' : 'ARWU'} numbers are better. This slice is ordered by{' '}
          {metric === 'qs_rank' ? 'QS world rank' : 'ARWU rank'}; other columns are for context.
        </p>
      </div>

      <div className="rankings-expand-bar rankings-expand-bar-below">
        <button
          type="button"
          className="rankings-expand-btn"
          disabled={!canMoreBelow}
          onClick={() => setBelowN((n) => Math.min(n + STEP, maxBelow))}
        >
          Show {STEP} more below (worse ranks)
        </button>
      </div>

      {unrankedLabels.length > 0 && (
        <p className="muted small rankings-unranked-footnote">
          Omitted from this ordering (no {metric === 'qs_rank' ? 'QS' : 'ARWU'} rank in Wikidata):{' '}
          {unrankedLabels.join(', ')}.
        </p>
      )}
    </section>
  )
}

function InstitutionTable({ rows }: { rows: InstitutionRankRow[] }) {
  return (
    <div className="rankings-table-wrap">
      <table className="rankings-inst-table">
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">Institution</th>
            <th scope="col">Region</th>
            <th scope="col" className="num">
              QS world rank
            </th>
            <th scope="col" className="num">
              QS year
            </th>
            <th scope="col" className="num">
              ARWU rank
            </th>
            <th scope="col" className="num">
              ARWU year
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={`${r.label}-${i}`} className={r.anchor ? 'rankings-anchor-row' : undefined}>
              <td>{i + 1}</td>
              <td>{r.label}</td>
              <td>{r.country || '—'}</td>
              <td className="num">{fmtRank(r.qs_rank)}</td>
              <td className="num">{r.qs_year ?? '—'}</td>
              <td className="num">{fmtRank(r.arwu_rank)}</td>
              <td className="num">{r.arwu_year ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="muted small rankings-table-note">
        Lower rank numbers are better. Empty cells mean Wikidata had no value for that edition.
      </p>
    </div>
  )
}

function InstitutionNeighborhoodViews({ rows }: { rows: InstitutionRankRow[] }) {
  return (
    <div className="rankings-neighborhood-stack">
      <NeighborhoodBlock
        metric="qs_rank"
        rows={rows}
        title="QS world university rankings (peer neighborhood)"
        note={`Around UW–Madison among peers that have a QS world rank. Initially ${INITIAL_SPAN} schools with better ranks and ${INITIAL_SPAN} with worse ranks.`}
      />
      <NeighborhoodBlock
        metric="arwu_rank"
        rows={rows}
        title="ARWU / Shanghai rankings (peer neighborhood)"
        note={`Around UW–Madison among peers that have an ARWU rank. Initially ${INITIAL_SPAN} schools above and ${INITIAL_SPAN} below on that scale.`}
      />
    </div>
  )
}

export function RankingsHubPanel({ bundle }: { bundle: RankingsHubBundle }) {
  const [sub, setSub] = useState<SubKey>('global')

  const majorsBundle: MajorRankingsBundle = {
    meta: {
      ...bundle.meta,
      methodology: `${bundle.sections.majors.title}. ${bundle.sections.majors.blurb}`,
    },
    entries: bundle.sections.majors.entries,
  }

  return (
    <div className="rankings-hub">
      <div className="rankings-subtabs" role="tablist" aria-label="Ranking views">
        {SUBS.map((s) => (
          <button
            key={s.id}
            type="button"
            role="tab"
            aria-selected={sub === s.id}
            className={sub === s.id ? 'rankings-subtab active' : 'rankings-subtab'}
            onClick={() => setSub(s.id)}
          >
            {s.label}
          </button>
        ))}
      </div>

      <div className="rankings-subpanel" role="tabpanel">
        {isInstitutionSub(sub) && (
          <>
            <h2 className="rankings-subtitle">{bundle.sections[sub].title}</h2>
            <p className="rankings-blurb">{bundle.sections[sub].blurb}</p>
            <p className="rankings-context-note muted small">
              Tables below are centered on UW–Madison within this peer list (not the full global
              publisher tables). Use expand to show more peers in each direction.
            </p>
            <InstitutionNeighborhoodViews key={sub} rows={bundle.sections[sub].institutions} />
          </>
        )}
        {sub === 'majors' && (
          <>
            <h2 className="rankings-subtitle">{bundle.sections.majors.title}</h2>
            <p className="rankings-blurb">{bundle.sections.majors.blurb}</p>
            <MajorRankingsPanel bundle={majorsBundle} />
          </>
        )}
      </div>
    </div>
  )
}
