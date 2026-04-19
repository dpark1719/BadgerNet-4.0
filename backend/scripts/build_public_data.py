#!/usr/bin/env python3
"""
Run public, no-login data fetches that populate frontend JSON.

  python build_public_data.py              # Full pipeline
  python build_public_data.py --skip-wikidata
  python build_public_data.py --only ipeds_origins

Steps use: requests, pandas (see backend/requirements.txt)
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
SCRIPTS = ROOT / "backend" / "scripts"


def run(script: str, *argv: str) -> None:
    path = SCRIPTS / script
    print(f"\n=== {script} {' '.join(argv)} ===")
    subprocess.run([PY, str(path), *argv], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--only",
        choices=(
            "ipeds_origins",
            "ipeds_intl",
            "wikidata",
            "outcomes",
            "openalex",
            "sources_index",
            "all",
        ),
        default="all",
    )
    ap.add_argument("--skip-wikidata", action="store_true")
    args = ap.parse_args()

    only = args.only
    full = only == "all"

    if full or only == "ipeds_origins":
        run(
            "build_origins_ipeds.py",
            "--years",
            "2019,2020,2021,2022",
        )
    if full or only == "ipeds_intl":
        run("build_international_proxy.py")
    if full or only == "outcomes":
        run("build_outcomes_scorecard.py")
    if full or only == "openalex":
        run("build_openalex_research.py")
    if only == "wikidata" or (full and not args.skip_wikidata):
        run("fetch_wikidata_notable.py")
    if full or only == "sources_index":
        run("build_sources_index.py")

    print("\nDone. Optional next steps:")
    print("  COLLEGE_SCORECARD_API_KEY=… python backend/scripts/build_outcomes_scorecard.py")
    print("  python backend/scripts/ingest_uw_postgrad.py --csv path/to/fds.csv")
    print("  python backend/scripts/ingest_international_destinations_csv.py --csv path/to/countries.csv")
    print("  python backend/scripts/ingest_industry_uw_csv.py --csv path/to/industry_bars.csv")
    print("  python backend/scripts/ingest_origins_level_csv.py --level graduate --csv path/to/cds_extract.csv")
    print("  python backend/scripts/merge_notable_manual.py --manual path/to/notable_extra.json")
    print("  python backend/scripts/linkedin_playwright_harvest.py --dry-run")
    print("Policy: backend/scripts/POLICY_AGGREGATES_ONLY.md")


if __name__ == "__main__":
    main()
