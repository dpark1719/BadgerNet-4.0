# BadgerNet 4.0 — backend / data (David)

Python tooling to download public data, normalize it, and emit chart bundles for the frontend.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Real public data (IPEDS + Wikidata)

From the **repository root**:

```bash
python3 backend/scripts/build_public_data.py
```

This refreshes:

- `origins_undergrad.json` — IPEDS **EF2022C** (first-time freshmen, US state of residence + foreign aggregate)
- `international.json` — IPEDS **DRVEF2022** `RMFRGNCN` (foreign-national **enrollment context**, not alumni destination)
- `notable.json` — Wikidata (educated at UW–Madison, Wikipedia link)

Details: [`scripts/DATA_PIPELINES.md`](scripts/DATA_PIPELINES.md)

## Sample / demo data

Regenerate **synthetic** JSON for UI development (overwrites many files — run before `build_public_data` only if you want an all-sample site):

```bash
python3 backend/scripts/generate_sample_data.py
```

## UW first-destination / post-grad

Tableau and PDFs change URLs often. Export a CSV and run:

```bash
python3 backend/scripts/ingest_uw_postgrad.py --csv /path/to/export.csv
```

Starting points: [data.wisc.edu — First Destination Survey](https://data.wisc.edu/first-destination-survey/), [careers.wisc.edu](https://careers.wisc.edu/first-destination-survey/).

## LinkedIn aggregates (no API)

1. Implement scraping in [`scripts/linkedin_playwright_harvest.py`](scripts/linkedin_playwright_harvest.py) (Playwright + `LINKEDIN_STORAGE_STATE`), **or** export counts manually.
2. Emit a CSV and run [`scripts/linkedin_aggregate_to_majors.py`](scripts/linkedin_aggregate_to_majors.py) → `frontend/public/data/majors/*.json`.

## Optional College Scorecard

```bash
export COLLEGE_SCORECARD_API_KEY=your_data_gov_key
python3 backend/scripts/fetch_college_scorecard.py
```

Writes reference JSON under `data/raw/` (does not replace tab bundles by itself).

## Layout

| Path | Purpose |
|------|---------|
| `lib/` | Shared helpers (e.g. FIPS labels) |
| `scripts/` | ETL entrypoints |
| `../data/raw/` | Download cache (gitignored except README) |

Copy `backend/.env.example` to `backend/.env` for local secrets (never commit `.env`).
