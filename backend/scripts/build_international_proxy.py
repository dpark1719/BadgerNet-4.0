#!/usr/bin/env python3
"""
Build international.json with **disclosed limitations**: IPEDS derived file
DRVEF gives a foreign-national count (RMFRGNCN) for the institution, not
"destination country after graduation."

Post-UW geography still requires LinkedIn-style aggregates or other surveys.
This script sets honest meta + a minimal bar from DRVEF for context.
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
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

    payload = {
        "meta": {
            "project": "BadgerNet 4.0",
            "tab": "international_outcomes",
            "snapshot_date": datetime.now().strftime("%Y-%m-%d"),
            "degree_level": "all",
            "source": "ipeds",
            "source_url": "https://nces.ed.gov/ipeds/datacenter/",
            "methodology": (
                f"DRVEF{args.year} field RMFRGNCN: count related to nonresident foreign students "
                "in IPEDS derived fall enrollment — **not** post-graduation destination. "
                "For country-of-destination after UW, use LinkedIn aggregate harvest + disclaimers."
            ),
            "disclaimer": (
                "This tab’s primary bar is an enrollment-related IPEDS aggregate, not ‘where alumni moved.’ "
                "Do not interpret as career migration statistics."
            ),
        },
        "charts": {
            "ipeds_foreign_context": {
                "type": "bar",
                "title": f"IPEDS foreign-national context (DRVEF{args.year}, UW–Madison) — not destination",
                "data": [
                    {"label": "RMFRGNCN (IPEDS derived)", "value": foreign},
                ],
            },
        },
    }

    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} (RMFRGNCN={foreign})")


if __name__ == "__main__":
    main()
