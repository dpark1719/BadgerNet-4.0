# Real data pipelines

Harvesting policy (no mass profile scraping): [POLICY_AGGREGATES_ONLY.md](POLICY_AGGREGATES_ONLY.md).

Run from repo root with `backend/requirements.txt` installed:

```bash
python3 -m pip install -r backend/requirements.txt
python3 backend/scripts/build_public_data.py
```

| Script | Output | Source |
|--------|--------|--------|
| [`build_origins_ipeds.py`](build_origins_ipeds.py) | `frontend/public/data/origins_undergrad.json` | IPEDS **EF{year}C** (first-time freshmen residence by state), UNITID **240444** |
| [`build_international_proxy.py`](build_international_proxy.py) | `frontend/public/data/international.json` | IPEDS **DRVEF{year}** `RMFRGNCN` (enrollment-related foreign context — **not** post-grad destination) |
| [`ingest_international_destinations_csv.py`](ingest_international_destinations_csv.py) | merges into `international.json` | **Your** country roll-up CSV → chart `aggregate_destination_proxy` (run after `build_international_proxy.py`) |
| [`fetch_wikidata_notable.py`](fetch_wikidata_notable.py) | `frontend/public/data/notable.json` | Wikidata SPARQL (`P69` = UW–Madison, Wikipedia sitelink); optional **P18** image + Wikipedia summary thumbnail; inferred **achievement** badges (Nobel, CEO, founder, etc.) |
| [`merge_notable_manual.py`](merge_notable_manual.py) | updates `notable.json` | **Your** `{ "entries": [...] }` JSON merged by name |
| [`fetch_college_scorecard.py`](fetch_college_scorecard.py) | `data/raw/scorecard_UW.json` | College Scorecard API (optional `COLLEGE_SCORECARD_API_KEY`) |
| [`ingest_uw_postgrad.py`](ingest_uw_postgrad.py) | `frontend/public/data/postgrad.json` | **Your** CSV: `credential_type,count` and/or **`institution,count`** (grad/PhD destinations); `--merge` overlays without dropping other charts |
| [`ingest_industry_uw_csv.py`](ingest_industry_uw_csv.py) | `frontend/public/data/industry.json` | **Your** CSV `chart_key,label,value` (e.g. `by_industry`, `top_employers`) |
| [`ingest_origins_level_csv.py`](ingest_origins_level_csv.py) | `origins_graduate.json` / `origins_doctorate.json` | **Your** CDS / UW Excel paste → CSV (`kind,label,value` or split state/country files) |
| [`linkedin_aggregate_to_majors.py`](linkedin_aggregate_to_majors.py) | `frontend/public/data/majors/*.json` + [`majors/index.json`](../../frontend/public/data/majors/index.json) | **Your** aggregate CSV; optional columns `major_label`, `major_cip`; ends by running index sync |
| [`sync_majors_index.py`](sync_majors_index.py) | `frontend/public/data/majors/index.json` | Scans `majors/*.json` (non-empty `charts`) so the Industry dropdown lists every slice on disk; run manually if you add/remove slice files without using `linkedin_aggregate_to_majors.py` |
| [`linkedin_playwright_harvest.py`](linkedin_playwright_harvest.py) | (local only; export CSV) | Playwright + `LINKEDIN_STORAGE_STATE` — use for **facet exports you are allowed to save**, not profile dumps |

**Industry / employers / pathways (all majors or by major)** are not in IPEDS. Use UW-published tables → `ingest_industry_uw_csv.py`, LinkedIn roll-ups → `linkedin_aggregate_to_majors.py`, or `generate_sample_data.py` for demos.

**Origins (graduate / doctorate)** by geography: UW **Common Data Set** (download PDF/Excel from [Common Data Set and rankings](https://data.wisc.edu/common-data-set-and-rankings/)), then `ingest_origins_level_csv.py`. Automated Box fetch is fragile; prefer manual download to `data/raw/`. EF2022C remains freshmen-only for UG IPEDS.
