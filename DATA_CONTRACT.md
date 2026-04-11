# BadgerNet 4.0 — data contract

Frontend and backend agree on JSON bundles under `frontend/public/data/`. Each file is self-contained for one tab (or shared metadata).

## Common `meta` object

| Field | Type | Description |
|--------|------|-------------|
| `project` | string | e.g. `BadgerNet 4.0` |
| `tab` | string | `industry` \| `postgrad` \| `international_outcomes` \| `origins` |
| `snapshot_date` | string | ISO date of data snapshot |
| `academic_year` | string? | e.g. `2023-24` if applicable |
| `degree_level` | string | `all` \| `undergraduate` \| `graduate` \| `doctorate` |
| `source` | string | `linkedin` \| `uw_survey` \| `ipeds` \| `sample` \| `mixed` |
| `source_url` | string? | Primary citation URL |
| `methodology` | string | Short human-readable note |
| `disclaimer` | string? | Bias / coverage warning |

## Chart payloads

### `industry.json`

```json
{
  "meta": { ... },
  "charts": {
    "by_industry": {
      "type": "bar",
      "title": "Alumni by industry (sample)",
      "data": [{ "label": "Technology", "value": 1200 }, ...]
    }
  }
}
```

### `postgrad.json`

```json
{
  "meta": { ... },
  "charts": {
    "continuation_rate": {
      "type": "metric",
      "title": "Continuing education (survey, sample %)",
      "value": 24.5,
      "unit": "percent"
    },
    "by_degree_type": {
      "type": "bar",
      "title": "Next credential type (sample)",
      "data": [{ "label": "Master’s", "value": 410 }, ...]
    }
  }
}
```

### `international.json`

```json
{
  "meta": { ... },
  "charts": {
    "destination_country": {
      "type": "bar",
      "title": "Post-UW location — country (sample, LinkedIn-proxy)",
      "data": [{ "label": "India", "value": 320 }, ...]
    }
  }
}
```

### `origins.json`

```json
{
  "meta": { ... },
  "charts": {
    "us_states": {
      "type": "bar",
      "title": "US home state — enrolled (sample, IPEDS-style)",
      "data": [{ "label": "WI", "value": 8200 }, ...]
    },
    "countries": {
      "type": "bar",
      "title": "Country of origin — international enrolled (sample)",
      "data": [{ "label": "China", "value": 1200 }, ...]
    }
  }
}
```

### `meta.json`

Site-wide strings and links (methodology page).

## Backend responsibilities

- Produce validated JSON into `frontend/public/data/`.
- Never commit PII or raw LinkedIn HTML; only aggregates.
- Document `filter_fingerprint` for LinkedIn-derived files in `meta.methodology` when applicable.

## Frontend responsibilities

- Fetch `/data/<file>.json` at runtime (or import for tests).
- Render `meta.disclaimer` prominently for LinkedIn-backed tabs.
