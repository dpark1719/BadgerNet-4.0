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
- `notable.json` — Wikidata (educated at UW–Madison, Wikipedia link); thumbnails from P18 / Wikipedia REST; optional `--skip-enrich` to skip API calls

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
# Grad/PhD schools: CSV with institution,count — use --merge to keep existing charts
```

Starting points: [data.wisc.edu — First Destination Survey](https://data.wisc.edu/first-destination-survey/), [careers.wisc.edu](https://careers.wisc.edu/first-destination-survey/).

## LinkedIn aggregates (no API)

1. Use LinkedIn (or similar) **facet / roll-up exports** you are permitted to save, **or** manual counts — not mass profile harvesting (see [`scripts/POLICY_AGGREGATES_ONLY.md`](scripts/POLICY_AGGREGATES_ONLY.md)).
2. Emit a CSV and run [`scripts/linkedin_aggregate_to_majors.py`](scripts/linkedin_aggregate_to_majors.py) → `frontend/public/data/majors/*.json` and refreshes `majors/index.json` (optional CSV columns `major_label`, `major_cip`). To rebuild the index only: [`scripts/sync_majors_index.py`](scripts/sync_majors_index.py).

## More CSV ingests

- **International destination proxy** (after `build_international_proxy.py`): [`ingest_international_destinations_csv.py`](scripts/ingest_international_destinations_csv.py) — `country,count` → chart `aggregate_destination_proxy`.
- **Industry / employers (all majors):** [`ingest_industry_uw_csv.py`](scripts/ingest_industry_uw_csv.py) — `chart_key,label,value`.
- **Grad / PhD origins:** [`ingest_origins_level_csv.py`](scripts/ingest_origins_level_csv.py) — paste from CDS Excel → `kind,label,value`.
- **Notable list:** [`merge_notable_manual.py`](scripts/merge_notable_manual.py) after Wikidata.

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
