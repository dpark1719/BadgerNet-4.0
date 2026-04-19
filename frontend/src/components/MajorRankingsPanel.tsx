import type { MajorRankingsBundle } from '../types/data'

function fmt(n: number) {
  return n.toLocaleString()
}

export function MajorRankingsPanel({ bundle }: { bundle: MajorRankingsBundle }) {
  return (
    <section className="major-rankings" aria-label="UW program list and ranks">
      <div className="major-rankings-scroll">
        <table className="major-rankings-table">
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Program (CIP)</th>
              <th scope="col" className="num">
                IPEDS awards
              </th>
              <th scope="col" className="num">
                Publisher rank
              </th>
              <th scope="col">Publisher</th>
              <th scope="col">Source</th>
            </tr>
          </thead>
          <tbody>
            {bundle.entries.map((row, i) => (
              <tr key={`${row.cipcode}-${i}`}>
                <td>{i + 1}</td>
                <td>
                  <span className="major-rankings-name">{row.program_label}</span>
                  <span className="major-rankings-cip mono">{row.cipcode}</span>
                </td>
                <td className="num">{fmt(row.ipeds_awards)}</td>
                <td className="num">
                  {row.publisher_rank != null ? row.publisher_rank : '—'}
                </td>
                <td>{row.publisher ?? '—'}</td>
                <td>
                  {row.source_url ? (
                    <a
                      className="link"
                      href={row.source_url}
                      target="_blank"
                      rel="noreferrer"
                    >
                      Link
                    </a>
                  ) : (
                    '—'
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
