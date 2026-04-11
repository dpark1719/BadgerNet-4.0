# BadgerNet 4.0 — backend / data (David)

Python tooling to download, normalize, and emit chart bundles for the frontend.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Generate sample data (no external downloads)

Writes JSON to `frontend/public/data/`:

```bash
python scripts/generate_sample_data.py
```

## Stubs (extend next)

| Script | Purpose |
|--------|---------|
| `scripts/ipeds_origins.py` | Instructions + placeholder for IPEDS → `origins_*.json` |
| `scripts/linkedin_harvest.py` | Placeholder for aggregate-only Playwright harvest (no API) |

Copy `backend/.env.example` to `backend/.env` for local automation vars (never commit `.env`).

## Layout

| Path | Purpose |
|------|---------|
| `scripts/generate_sample_data.py` | Deterministic sample bundles for UI dev |
| `scripts/` | IPEDS parsers, PDF extractors, LinkedIn rollup jobs |
| `../data/raw/` | Gitignored cache for CSVs / exports (create locally) |

## LinkedIn / automation

Keep output **aggregated only**; document filters in `meta.methodology` and `meta.filter_fingerprint`. Do not commit credentials, `storage_state`, or raw HTML.
