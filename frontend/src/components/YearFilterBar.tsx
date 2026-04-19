type Props = {
  years: string[]
  selected: Set<string>
  onToggle: (year: string) => void
  onSelectAll: () => void
}

export function YearFilterBar({ years, selected, onToggle, onSelectAll }: Props) {
  if (years.length === 0) return null

  return (
    <div className="year-filter" role="group" aria-label="Filter by cohort year">
      <span className="year-filter-label">Cohort years</span>
      <div className="year-filter-actions">
        <button
          type="button"
          className="link-button year-filter-all"
          onClick={onSelectAll}
        >
          Select all
        </button>
      </div>
      <div className="year-filter-checks">
        {years.map((y) => (
          <label key={y} className="year-filter-item">
            <input
              type="checkbox"
              checked={selected.has(y)}
              onChange={() => {
                onToggle(y)
              }}
            />
            <span>{y}</span>
          </label>
        ))}
      </div>
    </div>
  )
}
