# BadgerNet 4.0 — data contract

Frontend and backend agree on JSON bundles under `frontend/public/data/`. Each file is self-contained for one **top-level tab** (or shared metadata).

## Tab IDs and files

| `meta.tab` / nav `id` | File |
|----------------------|------|
| `industry` | `industry.json` |
| `postgrad` | `postgrad.json` |
| `international_outcomes` | `international.json` |
| `origins_undergraduate` | `origins_undergrad.json` |
| `origins_graduate` | `origins_graduate.json` |
| `origins_doctorate` | `origins_doctorate.json` |

## Common `meta` object

| Field | Type | Description |
|--------|------|-------------|
| `project` | string | e.g. `BadgerNet 4.0` |
| `tab` | string | Matches table above |
| `snapshot_date` | string | ISO date of data snapshot |
| `academic_year` | string? | e.g. `2023-24` if applicable |
| `degree_level` | string | `all` \| `undergraduate` \| `graduate` \| `doctorate` |
| `source` | string | `linkedin` \| `uw_survey` \| `ipeds` \| `sample` \| `mixed` |
| `source_url` | string? | Primary citation URL |
| `methodology` | string | Short human-readable note; for LinkedIn include **filter recipe** / `filter_fingerprint` text |
| `disclaimer` | string? | Bias / coverage warning |
| `filter_fingerprint` | string? | Optional stable hash or human summary of LinkedIn filters used |

## International outcomes tab — population

Charts in `international.json` should describe methodology for: **non–U.S. citizens who originated from abroad** (pre-UW origin outside the United States), then **post-UW destination** (e.g. country/region). LinkedIn proxies are approximate; state limitations in `meta.disclaimer`.

## Chart types

### `bar`

```json
{
  "type": "bar",
  "title": "…",
  "data": [{ "label": "Technology", "value": 1200 }]
}
```

### `metric`

```json
{
  "type": "metric",
  "title": "…",
  "value": 24.5,
  "unit": "percent"
}
```

### `trend` (1y / 5y / 10y style series over calendar year)

Multiple series share the same `year` axis. Each row is one calendar year (or reporting year). Series keys are arbitrary strings; `series` tells the UI which keys to plot.

```json
{
  "type": "trend",
  "title": "Sample trend (synthetic)",
  "x_key": "year",
  "data": [
    { "year": 2016, "w1y": 12.1, "w5y": 11.4, "w10y": 10.9 },
    { "year": 2017, "w1y": 12.3, "w5y": 11.5, "w10y": 11.0 }
  ],
  "series": [
    { "dataKey": "w1y", "label": "1-year window", "color": "#c5050c" },
    { "dataKey": "w5y", "label": "5-year window", "color": "#1e3a8a" },
    { "dataKey": "w10y", "label": "10-year window", "color": "#047857" }
  ]
}
```

- **`x_key`:** defaults to `year` if omitted.
- **Values** may be counts or percentages; label them in `title` / axis copy.

### `meta.json`

Site-wide strings, **six** tab entries (`id` + `label`), links (`github_repo`, `github_project`).

## Backend responsibilities

- Produce validated JSON into `frontend/public/data/`.
- Never commit PII or raw LinkedIn HTML; only aggregates.
- Document LinkedIn filters in `meta.methodology` and optional `meta.filter_fingerprint`.

## Frontend responsibilities

- Fetch `/data/<file>.json` at runtime.
- Render `meta.disclaimer` prominently for LinkedIn-backed or sample tabs.
- Support six top-level tabs; tab bar should scroll horizontally on narrow viewports.
