import { useMemo } from 'react'
import type { MajorRankEntry, MajorRankingsBundle } from '../types/data'

function fmt(n: number) {
  return n.toLocaleString()
}

const MAX_PUBLISHER_RANK = 10

function groupByPublisherRank(entries: MajorRankEntry[]): { rank: number; programs: MajorRankEntry[] }[] {
  const byRank = new Map<number, MajorRankEntry[]>()
  for (const e of entries) {
    const r = e.publisher_rank
    if (r == null || r < 1 || r > MAX_PUBLISHER_RANK) continue
    const k = Math.floor(Number(r))
    if (!byRank.has(k)) byRank.set(k, [])
    byRank.get(k)!.push(e)
  }
  for (const list of byRank.values()) {
    list.sort((a, b) => a.program_label.localeCompare(b.program_label))
  }
  return [...byRank.keys()]
    .sort((a, b) => a - b)
    .map((rank) => ({ rank, programs: byRank.get(rank)! }))
}

export function MajorRankingsPanel({ bundle }: { bundle: MajorRankingsBundle }) {
  const tiers = useMemo(() => groupByPublisherRank(bundle.entries), [bundle.entries])

  if (tiers.length === 0) {
    return (
      <section className="major-rankings" aria-label="UW top publisher-ranked programs">
        <p className="muted major-rankings-empty">
          No UW programs in this bundle have a publisher rank between 1 and {MAX_PUBLISHER_RANK}{' '}
          (vs other institutions). Add rows to <code className="mono">data/raw/major_ranks.csv</code>{' '}
          with <code className="mono">cipcode</code> and <code className="mono">publisher_rank</code>, then
          run <code className="mono">python3 backend/scripts/harvest_rankings.py</code>.
        </p>
      </section>
    )
  }

  return (
    <section className="major-rankings" aria-label="UW top publisher-ranked programs">
      <div className="major-rankings-scroll">
        <table className="major-rankings-table">
          <thead>
            <tr>
              <th scope="col">Program</th>
              <th scope="col" className="num">
                IPEDS awards
              </th>
              <th scope="col">Publisher</th>
              <th scope="col">Source</th>
            </tr>
          </thead>
          {tiers.map(({ rank, programs }) => (
            <tbody key={rank}>
              <tr className="major-rankings-tier">
                <td colSpan={4}>
                  <span className="major-rankings-tier-label">National / publisher rank {rank}</span>
                  <span className="major-rankings-tier-note muted small">
                    {programs.length} UW program{programs.length === 1 ? '' : 's'} at this rank
                  </span>
                </td>
              </tr>
              {programs.map((row) => (
                <tr key={`${row.cipcode}-${rank}`}>
                  <td>
                    <span className="major-rankings-name">{row.program_label}</span>
                    <span className="major-rankings-cip mono" title="IPEDS CIP-2020 code">
                      {row.cipcode}
                    </span>
                  </td>
                  <td className="num">{fmt(row.ipeds_awards)}</td>
                  <td>{row.publisher ?? '—'}</td>
                  <td>
                    {row.source_url ? (
                      <a className="link" href={row.source_url} target="_blank" rel="noreferrer">
                        Link
                      </a>
                    ) : (
                      '—'
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          ))}
        </table>
      </div>
    </section>
  )
}
