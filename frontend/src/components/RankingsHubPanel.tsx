import { useMemo, useState } from 'react'
import type {
  InstitutionRankRow,
  MajorRankingsBundle,
  RankingsHubBundle,
  RankSurroundBand,
} from '../types/data'
import { MajorRankingsPanel } from './MajorRankingsPanel'
import './RankingsHubPanel.css'

type SubKey = 'global' | 'us' | 'public' | 'majors'

/** Peers to show on each side of UW (closest in this ranking); expand adds another step each way. */
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

/** Closest `countAbove` peers with better ranks (lower numbers), then anchor, then closest `countBelow` worse peers. */
function windowClosestToAnchor(
  sortedAsc: InstitutionRankRow[],
  anchorIdx: number,
  countAbove: number,
  countBelow: number,
): InstitutionRankRow[] {
  const start = Math.max(0, anchorIdx - countAbove)
  const end = Math.min(sortedAsc.length, anchorIdx + countBelow + 1)
  return sortedAsc.slice(start, end)
}

function offsetVsUwLabel(rowIndex: number, anchorIndexInWindow: number): string {
  const d = rowIndex - anchorIndexInWindow
  if (d === 0) return '0'
  return d > 0 ? `+${d}` : String(d)
}

function focalRank(r: InstitutionRankRow, metric: 'qs_rank' | 'arwu_rank'): number | null {
  const v = r[metric]
  return v == null ? null : v
}

function deltaRankLabel(r: InstitutionRankRow, metric: 'qs_rank' | 'arwu_rank', center: number): string {
  const rk = focalRank(r, metric)
  if (rk == null) return '—'
  const d = rk - center
  if (d === 0) return '0'
  return d > 0 ? `+${d}` : String(d)
}

function NeighborhoodWikidataBand({
  band,
  metric,
  title,
  note,
}: {
  band: RankSurroundBand
  metric: 'qs_rank' | 'arwu_rank'
  title: string
  note: string
}) {
  const center = band.center_rank
  const bw = band.band_half_width
  const [aboveSpan, setAboveSpan] = useState(INITIAL_SPAN)
  const [belowSpan, setBelowSpan] = useState(INITIAL_SPAN)

  const rankMin = Math.max(1, center - aboveSpan)
  const rankMax = center + belowSpan

  const windowRows = useMemo(() => {
    return band.institutions
      .filter((r) => {
        const rk = focalRank(r, metric)
        if (rk == null) return false
        return rk >= rankMin && rk <= rankMax
      })
      .sort((a, b) => {
        const ar = focalRank(a, metric)
        const br = focalRank(b, metric)
        if (ar != null && br != null && ar !== br) return (ar as number) - (br as number)
        return a.label.localeCompare(b.label)
      })
  }, [band.institutions, metric, rankMin, rankMax])

  const presentRanks = new Set(
    windowRows.map((r) => focalRank(r, metric)).filter((n): n is number => n != null),
  )
  const missingRanks: number[] = []
  for (let rk = rankMin; rk <= rankMax; rk++) {
    if (!presentRanks.has(rk)) missingRanks.push(rk)
  }

  const maxAboveSpan = Math.min(bw, Math.max(0, center - 1))
  const canMoreAbove = aboveSpan < maxAboveSpan
  const canMoreBelow = belowSpan < bw

  const editionLabel = metric === 'qs_rank' ? 'QS world' : 'ARWU'

  return (
    <section className="rankings-neighborhood" aria-labelledby={`${metric}-wd-title`}>
      <h3 className="rankings-neighborhood-title" id={`${metric}-wd-title`}>
        {title}
      </h3>
      <p className="rankings-neighborhood-note muted small">{note}</p>

      <div className="rankings-expand-bar">
        <button
          type="button"
          className="rankings-expand-btn"
          disabled={!canMoreAbove}
          onClick={() => setAboveSpan((s) => Math.min(s + STEP, bw, Math.max(0, center - 1)))}
        >
          Show next {STEP} ranks (better / lower number)
        </button>
        <span className="rankings-expand-hint muted small">
          Integer window [{rankMin}, {rankMax}] around UW at {editionLabel} rank {center}
          {band.year ? ` (${band.year} statement year in Wikidata)` : ''}.
        </span>
      </div>

      <div className="rankings-table-wrap">
        <table className="rankings-inst-table">
          <thead>
            <tr>
              <th scope="col" className="num" title="Difference from UW’s rank number in this column">
                Δ rank
              </th>
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
              <tr
                key={r.qid ? `${r.qid}-${focalRank(r, metric)}` : `${r.label}-${metric}-${i}`}
                className={r.anchor ? 'rankings-anchor-row' : undefined}
              >
                <td className="num">{deltaRankLabel(r, metric, center)}</td>
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
          Rows are institutions in Wikidata with a {editionLabel} rank in this integer window (not the
          small peer-only list). Lower {editionLabel} numbers are better. Some rank integers may have
          no row if Wikidata has no statement for that place.
        </p>
      </div>

      <div className="rankings-expand-bar rankings-expand-bar-below">
        <button
          type="button"
          className="rankings-expand-btn"
          disabled={!canMoreBelow}
          onClick={() => setBelowSpan((s) => Math.min(s + STEP, bw))}
        >
          Show next {STEP} ranks (worse / higher number)
        </button>
      </div>

      {missingRanks.length > 0 && missingRanks.length <= 24 && (
        <p className="muted small rankings-unranked-footnote">
          No Wikidata row in this window for rank{missingRanks.length === 1 ? '' : 's'}:{' '}
          {missingRanks.join(', ')}.
        </p>
      )}
    </section>
  )
}

function NeighborhoodPeerSlice({
  rows,
  metric,
  title,
  peerNote,
}: {
  rows: InstitutionRankRow[]
  metric: 'qs_rank' | 'arwu_rank'
  title: string
  peerNote: string
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
    idx >= 0 ? windowClosestToAnchor(sortedRanked, idx, effAbove, effBelow) : sortedRanked

  const anchorInWindow = windowRows.findIndex((r) => r.anchor)
  const anchorInWindowFallback = windowRows.findIndex(
    (r) => /UW/i.test(r.label) && /Madison/i.test(r.label),
  )
  const anchorColIdx = anchorInWindow >= 0 ? anchorInWindow : anchorInWindowFallback

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
      <p className="rankings-neighborhood-note muted small">{peerNote}</p>

      <div className="rankings-expand-bar">
        <button
          type="button"
          className="rankings-expand-btn"
          disabled={!canMoreAbove}
          onClick={() => setAboveN((n) => Math.min(n + STEP, maxAbove))}
        >
          Show next {STEP} peers (better rank)
        </button>
        <span className="rankings-expand-hint muted small">
          {idx >= 0
            ? `Up to ${effAbove} peers directly above UW and ${effBelow} directly below in this ${metric === 'qs_rank' ? 'QS' : 'ARWU'} order (closest in the peer list).`
            : null}
        </span>
      </div>

      <div className="rankings-table-wrap">
        <table className="rankings-inst-table">
          <thead>
            <tr>
              <th scope="col" className="num" title="Steps from UW in this peer ordering (0 = UW)">
                vs UW
              </th>
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
                <td className="num">
                  {anchorColIdx >= 0 ? offsetVsUwLabel(i, anchorColIdx) : '—'}
                </td>
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
          Show next {STEP} peers (worse rank)
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

function InstitutionNeighborhoodViews({
  rows,
  bundle,
}: {
  rows: InstitutionRankRow[]
  bundle: RankingsHubBundle
}) {
  const qsBand = bundle.rank_surround?.qs
  const arBand = bundle.rank_surround?.arwu
  return (
    <div className="rankings-neighborhood-stack">
      {qsBand && qsBand.institutions.length > 0 ? (
        <NeighborhoodWikidataBand
          band={qsBand}
          metric="qs_rank"
          title="QS world university rankings (around UW’s rank)"
          note={`Schools whose Wikidata QS world rank falls in an integer window around UW (${qsBand.year ?? '—'} statement year), matching the published rank ladder—not the short peer list.`}
        />
      ) : (
        <NeighborhoodPeerSlice
          metric="qs_rank"
          rows={rows}
          title="QS world university rankings (peer list)"
          peerNote={`No Wikidata rank band in this bundle: showing the ${INITIAL_SPAN} closest peers in this tab that have a QS rank.`}
        />
      )}
      {arBand && arBand.institutions.length > 0 ? (
        <NeighborhoodWikidataBand
          band={arBand}
          metric="arwu_rank"
          title="ARWU / Shanghai rankings (around UW’s rank)"
          note={`Schools whose Wikidata ARWU rank falls in an integer window around UW (${arBand.year ?? '—'} statement year).`}
        />
      ) : (
        <NeighborhoodPeerSlice
          metric="arwu_rank"
          rows={rows}
          title="ARWU / Shanghai rankings (peer list)"
          peerNote={`No Wikidata rank band in this bundle: showing the ${INITIAL_SPAN} closest peers in this tab that have an ARWU rank.`}
        />
      )}
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
              QS and ARWU neighborhood tables use Wikidata rows near UW’s published rank (integer
              window). The peer list above is only for the summary comparison tables elsewhere on this
              tab.
            </p>
            <InstitutionNeighborhoodViews key={sub} rows={bundle.sections[sub].institutions} bundle={bundle} />
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
