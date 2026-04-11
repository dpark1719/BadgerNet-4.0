# Real data pipelines

Run from repo root with `backend/requirements.txt` installed:

```bash
python3 -m pip install -r backend/requirements.txt
python3 backend/scripts/build_public_data.py
```

| Script | Output | Source |
|--------|--------|--------|
| [`build_origins_ipeds.py`](build_origins_ipeds.py) | `frontend/public/data/origins_undergrad.json` | IPEDS **EF{year}C** (first-time freshmen residence by state), UNITID **240444** |
| [`build_international_proxy.py`](build_international_proxy.py) | `frontend/public/data/international.json` | IPEDS **DRVEF{year}** `RMFRGNCN` (enrollment-related foreign context — **not** post-grad destination) |
| [`fetch_wikidata_notable.py`](fetch_wikidata_notable.py) | `frontend/public/data/notable.json` | Wikidata SPARQL (`P69` = UW–Madison, Wikipedia sitelink) |
| [`fetch_college_scorecard.py`](fetch_college_scorecard.py) | `data/raw/scorecard_UW.json` | College Scorecard API (optional `COLLEGE_SCORECARD_API_KEY`) |
| [`ingest_uw_postgrad.py`](ingest_uw_postgrad.py) | `frontend/public/data/postgrad.json` | **Your** CSV export from UW FDS / Tableau |
| [`linkedin_aggregate_to_majors.py`](linkedin_aggregate_to_majors.py) | `frontend/public/data/majors/*.json` | **Your** aggregate CSV from harvest |
| [`linkedin_playwright_harvest.py`](linkedin_playwright_harvest.py) | (you implement DOM → CSV) | Playwright + `LINKEDIN_STORAGE_STATE` |

**Industry / employers / pathways (all majors or by major)** are not in IPEDS. Use LinkedIn aggregates → CSV → `linkedin_aggregate_to_majors.py`, or keep `generate_sample_data.py` for demos.

**Origins (graduate / doctorate)** by home state need additional IPEDS tables or CDS; EF2022C is freshmen-only.
