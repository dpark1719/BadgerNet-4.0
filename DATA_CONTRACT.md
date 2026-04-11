# BadgerNet 4.0 — data contract

Frontend and backend agree on JSON bundles under `frontend/public/data/`. Each file is self-contained for one **top-level tab** (or shared metadata), except **per-major slices** under `majors/`.

## Tab IDs and files

| `meta.tab` / nav `id` | File |
|----------------------|------|
| `industry` | `industry.json` (all majors); see **Major filter** below |
| `postgrad` | `postgrad.json` |
| `international_outcomes` | `international.json` |
| `origins_undergraduate` | `origins_undergrad.json` |
| `origins_graduate` | `origins_graduate.json` |
| `origins_doctorate` | `origins_doctorate.json` |
| `notable_alumni` | `notable.json` (uses `entries`, not `charts`) |
| `vizualive` | [`vizualive.json`](frontend/public/data/vizualive.json) (uses `roots` tree, not `charts`) |

## Major filter (Industry tab)

- **Index:** [`majors/index.json`](frontend/public/data/majors/index.json) — `{ "majors": [{ "id": "computer_science", "label": "…", "cip": "…" }] }` (no `all` row; UI adds “All majors”).
- **Per-major bundle:** [`majors/{id}.json`](frontend/public/data/majors/) — same shape as a normal tab: `{ "meta", "charts" }` with `meta.tab` = `industry` and optional **`meta.major_id`** matching `id`.
- When the user selects **All majors**, load [`industry.json`](frontend/public/data/industry.json). When a specific major is selected on the **Industry** tab, load `majors/{id}.json` instead.
- Other tabs ignore major selection in v1 unless you add major-aware files later.

## Common `meta` object

| Field | Type | Description |
|--------|------|-------------|
| `project` | string | e.g. `BadgerNet 4.0` |
| `tab` | string | Matches table above |
| `major_id` | string? | Set on `majors/*.json` slices (e.g. `computer_science`) |
| `snapshot_date` | string | ISO date of data snapshot |
| `academic_year` | string? | e.g. `2023-24` if applicable |
| `degree_level` | string | `all` \| `undergraduate` \| `graduate` \| `doctorate` |
| `source` | string | `linkedin` \| `uw_survey` \| `ipeds` \| `sample` \| `mixed` \| `wikidata` |
| `source_url` | string? | Primary citation URL |
| `methodology` | string | Short human-readable note; for LinkedIn include **filter recipe** / `filter_fingerprint` text |
| `disclaimer` | string? | Bias / coverage warning |
| `filter_fingerprint` | string? | Optional stable hash or human summary of LinkedIn filters used |

## International outcomes tab — population

Charts in `international.json` should describe methodology for: **non–U.S. citizens who originated from abroad** (pre-UW origin outside the United States), then **post-UW destination** (e.g. country/region). LinkedIn proxies are approximate; state limitations in `meta.disclaimer`.

Common chart keys:

- `ipeds_foreign_context` — IPEDS DRVEF enrollment-related aggregate (not destination).
- `aggregate_destination_proxy` — user-supplied country/region roll-up (e.g. LinkedIn Insights export), merged by `ingest_international_destinations_csv.py`.

## Chart types

### `bar`

```json
{
  "type": "bar",
  "title": "…",
  "data": [{ "label": "Technology", "value": 1200 }]
}
```

Use for **top employers** (e.g. chart key `top_employers`) with employer names as `label` and counts as `value`.

### `metric`

```json
{
  "type": "metric",
  "title": "…",
  "value": 24.5,
  "unit": "percent"
}
```

### `trend`

(unchanged — see previous version; `x_key`, `data`, `series`.)

### `sankey` (career flow)

Top **K** nodes and links from aggregate transitions (e.g. early industry bucket → current industry bucket). Cap nodes/links for readability and privacy.

```json
{
  "type": "sankey",
  "title": "Common career transitions (sample)",
  "nodes": [
    { "id": "intern_tech", "label": "Early — intern (tech)" },
    { "id": "swe_mid", "label": "Mid — software engineer" }
  ],
  "links": [
    { "source": "intern_tech", "target": "swe_mid", "value": 420 }
  ]
}
```

- **`id`:** stable string keys; **`links.source` / `target`** reference node `id`s.
- **`value`:** flow magnitude (count or weighted count).

## Notable alumni — `notable.json`

Not a `charts` object. Shape:

```json
{
  "meta": { ... },
  "entries": [
    {
      "name": "…",
      "role_title": "…",
      "organization": "…",
      "notability": "widely_cited" | "senior_role" | "other",
      "source_url": "https://…",
      "source_type": "wikipedia" | "uw_news" | "linkedin_aggregate" | "other",
      "year": "optional",
      "photo_url": "optional"
    }
  ]
}
```

- **Every** displayed row must have a **`source_url`**.
- Cap list length (e.g. ≤100) in production.
- LinkedIn-derived rows require human review or strict rules before inclusion; never ship raw profile dumps.

## Vizualive — `vizualive.json`

Interactive bubble drill-down (Agar-style force layout in the UI). Not a chart bundle.

```json
{
  "meta": { ... },
  "roots": [
    {
      "id": "postgrad",
      "label": "Postgrad education",
      "count": 100,
      "children": [
        {
          "id": "pg_ms_gt",
          "label": "Georgia Tech",
          "subtitle": "UW undergrad → M.S. (different institution)",
          "count": 40,
          "children": []
        }
      ]
    }
  ]
}
```

- **`roots`:** exactly three top-level nodes in v1: post-grad outcomes, job outcomes, country outcomes (ids are stable for analytics).
- Each node: **`id`**, **`label`**, **`count`** (non-negative integer). **`subtitle`** optional for path context.
- **`children`:** array of child nodes; omit or use `[]` for leaves. Parent **`count`** should equal the sum of child **`count`** values (enforced in QA / CI when possible).
- Backend may later replace synthetic trees with real path rollups keyed by `id`.

### `meta.json`

Site-wide strings, tab entries (`id` + `label`) for each nav item, links (`github_repo`, `github_project`).

## Backend responsibilities

- Produce `majors/index.json`, `majors/{id}.json`, `notable.json`, `vizualive.json`, and tab JSON into `frontend/public/data/`.
- Never commit PII or raw LinkedIn HTML; only aggregates.
- Optional: [`backend/scripts/wikidata_notable.py`](backend/scripts/wikidata_notable.py) seeds `entries` from Wikidata SPARQL; optional: [`backend/scripts/linkedin_major_slices.py`](backend/scripts/linkedin_major_slices.py) builds `majors/*.json` from harvest aggregates.

## Frontend responsibilities

- Fetch `/data/<file>.json` at runtime; for Industry + major ≠ all, fetch `/data/majors/{id}.json`.
- Keep URL query `?major=` in sync for shareable state.
- Render `meta.disclaimer` prominently for LinkedIn-backed or sample tabs.
- Tab bar scrolls horizontally on narrow viewports. World map reads sample flows from `map_destinations.json` (not the IPEDS chart on `international.json`). Vizualive reads `vizualive.json`.
