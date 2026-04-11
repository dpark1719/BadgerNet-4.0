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

## Layout

| Path | Purpose |
|------|---------|
| `scripts/generate_sample_data.py` | Deterministic sample bundles for UI dev |
| `scripts/` | Add IPEDS pulls, PDF parsers, LinkedIn rollup jobs here |
| `../data/raw/` | Gitignored cache for CSVs / exports (create locally) |

## LinkedIn / scraping

If you add harvest scripts, keep output **aggregated only** and document filters in each JSON `meta.methodology`. Do not commit credentials or raw profile dumps.
