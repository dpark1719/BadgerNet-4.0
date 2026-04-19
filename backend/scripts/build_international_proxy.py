#!/usr/bin/env python3
"""
Build international.json with:
- A **sample** post-graduation destination bar chart by country (replace with
  `ingest_international_destinations_csv.py` for real LinkedIn/survey roll-ups).
- IPEDS DRVEF RMFRGNCN as **enrollment context** (not destination).
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend.lib.cohort_year_split import bars_with_years  # noqa: E402

RAW = ROOT / "data" / "raw" / "ipeds"
OUT = ROOT / "frontend" / "public" / "data" / "international.json"

UNITID = 240444
ZIP_TMPL = "https://nces.ed.gov/ipeds/datacenter/data/DRVEF{year}.zip"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2022)
    args = ap.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)
    zpath = RAW / f"DRVEF{args.year}.zip"
    if not zpath.exists():
        url = ZIP_TMPL.format(year=args.year)
        print(f"Downloading {url} …")
        r = requests.get(url, timeout=300)
        r.raise_for_status()
        zpath.write_bytes(r.content)

    needle = f"drvef{args.year}.csv".lower()
    with zipfile.ZipFile(zpath, "r") as zf:
        names = [
            n
            for n in zf.namelist()
            if n.lower().endswith(".csv") and needle in n.lower() and "_rv" not in n.lower()
        ]
        if not names:
            raise FileNotFoundError(needle)
        names.sort()
        df = pd.read_csv(zf.open(names[0]), dtype=str, low_memory=False)

    row = df[df["UNITID"].astype(str).str.strip() == str(UNITID)]
    if row.empty:
        raise SystemExit(f"UNITID {UNITID} not in DRVEF{args.year}")
    r0 = row.iloc[0]
    foreign = int(float(r0.get("RMFRGNCN", 0) or 0))

    from datetime import datetime

    post_grad_dest = bars_with_years(
        [
            {"label": "United States", "value": 1850},
            {"label": "India", "value": 620},
            {"label": "China", "value": 510},
            {"label": "Canada", "value": 280},
            {"label": "South Korea", "value": 195},
            {"label": "United Kingdom", "value": 142},
            {"label": "Germany", "value": 88},
            {"label": "Japan", "value": 76},
            {"label": "Other / unknown", "value": 890},
        ],
        seed=77_001,
    )

    payload = {
        "meta": {
            "project": "BadgerNet 4.0",
            "tab": "international_outcomes",
            "snapshot_date": datetime.now().strftime("%Y-%m-%d"),
            "degree_level": "all",
            "academic_year": "2016–25 cohorts (pooled; filter years in UI)",
            "source": "mixed",
            "source_url": "https://nces.ed.gov/ipeds/datacenter/",
            "methodology": (
                f"**Post-graduation destinations (sample):** The chart “Where alumni went after UW” is a "
                f"synthetic multi-year aggregate by country for UI demonstration only — not official UW "
                f"migration or placement statistics. Replace via `ingest_international_destinations_csv.py` "
                f"with your LinkedIn or survey roll-up. "
                f"**IPEDS context:** DRVEF{args.year} field RMFRGNCN counts nonresident foreign students in "
                f"derived fall enrollment — **not** where graduates moved after completing their program. "
                f"**Open Doors context:** Rounded U.S.-level totals published by IIE Open Doors "
                f"(https://opendoorsdata.org/) for scale only — not UW-specific enrollment or mobility."
            ),
            "disclaimer": (
                "The destination-country chart is illustrative demo data. The IPEDS bar is enrollment-related "
                "only, not career geography. Open Doors bars are national-level IIE aggregates — not UW counts. "
                "Do not sum or compare cohorts across these charts as one population."
            ),
        },
        "charts": {
            "post_graduation_destination_country": {
                "type": "bar",
                "title": "Where international alumni went after UW — by country (sample aggregate)",
                "data": post_grad_dest,
            },
            "ipeds_foreign_context": {
                "type": "bar",
                "title": f"IPEDS foreign-national context (DRVEF{args.year}, UW–Madison) — not destination",
                "data": [
                    {"label": "RMFRGNCN (IPEDS derived)", "value": foreign},
                ],
            },
            "open_doors_national_context": {
                "type": "bar",
                "title": "National mobility context (IIE Open Doors — U.S. totals, not UW)",
                "data": [
                    {
                        "label": "International students in the U.S. (≈2023/24 headline total)",
                        "value": 1106104,
                    },
                    {
                        "label": "U.S. students studying abroad for credit (≈2022/23 headline total)",
                        "value": 280782,
                    },
                ],
            },
        },
    }

    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} (RMFRGNCN={foreign})")


if __name__ == "__main__":
    main()
