#!/usr/bin/env python3
"""
Run public, no-login data fetches that populate frontend JSON.

  python build_public_data.py              # IPEDS origins + international proxy + Wikidata notable
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


def run(name: str) -> None:
    path = SCRIPTS / name
    print(f"\n=== {name} ===")
    subprocess.run([PY, str(path)], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--only",
        choices=("ipeds_origins", "ipeds_intl", "wikidata", "all"),
        default="all",
    )
    ap.add_argument("--skip-wikidata", action="store_true")
    args = ap.parse_args()

    if args.only in ("all", "ipeds_origins"):
        run("build_origins_ipeds.py")
    if args.only in ("all", "ipeds_intl"):
        run("build_international_proxy.py")
    if args.only == "all" and not args.skip_wikidata:
        run("fetch_wikidata_notable.py")

    print("\nDone. Optional next steps:")
    print("  COLLEGE_SCORECARD_API_KEY=… python backend/scripts/fetch_college_scorecard.py")
    print("  python backend/scripts/ingest_uw_postgrad.py --csv path/to/fds.csv")
    print("  python backend/scripts/ingest_international_destinations_csv.py --csv path/to/countries.csv")
    print("  python backend/scripts/ingest_industry_uw_csv.py --csv path/to/industry_bars.csv")
    print("  python backend/scripts/ingest_origins_level_csv.py --level graduate --csv path/to/cds_extract.csv")
    print("  python backend/scripts/merge_notable_manual.py --manual path/to/notable_extra.json")
    print("  python backend/scripts/linkedin_playwright_harvest.py --dry-run")
    print("Policy: backend/scripts/POLICY_AGGREGATES_ONLY.md")


if __name__ == "__main__":
    main()
