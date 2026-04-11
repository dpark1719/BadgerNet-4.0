#!/usr/bin/env python3
"""
Post-grad / first-destination style metrics from **local** UW exports.

UW–Madison publishes First Destination Survey primarily via Tableau / web pages
(e.g. https://data.wisc.edu/first-destination-survey/), not a single stable PDF.

Usage:
  1. Export a CSV from Tableau or copy tables from a PDF into a CSV with columns:
       credential_type,count   OR   metric,value
  2. Run:
       python ingest_uw_postgrad.py --csv /path/to/fds_export.csv

If --csv is omitted, prints instructions only.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "frontend" / "public" / "data" / "postgrad.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, help="Local CSV from UW FDS / outcomes export")
    args = ap.parse_args()

    if not args.csv or not args.csv.is_file():
        print(__doc__)
        print("\nOfficial starting points:")
        print("  https://data.wisc.edu/first-destination-survey/")
        print("  https://careers.wisc.edu/first-destination-survey/")
        return

    by_label: dict[str, int] = defaultdict(int)
    with args.csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            keys = {k.lower().strip(): v for k, v in row.items() if k}
            label = keys.get("credential_type") or keys.get("label") or keys.get("type")
            val = keys.get("count") or keys.get("value")
            if not label or val is None:
                continue
            try:
                by_label[str(label).strip()] += int(float(val))
            except ValueError:
                continue

    if not by_label:
        print("No numeric rows parsed; expected columns like credential_type,count")
        return

    data = [{"label": k, "value": v} for k, v in sorted(by_label.items(), key=lambda x: -x[1])]

    payload = {
        "meta": {
            "project": "BadgerNet 4.0",
            "tab": "postgrad",
            "snapshot_date": datetime.now().strftime("%Y-%m-%d"),
            "degree_level": "all",
            "source": "uw_survey",
            "source_url": "https://data.wisc.edu/first-destination-survey/",
            "methodology": f"Imported from local CSV: {args.csv.name}. Verify against official UW definitions.",
            "disclaimer": "User-supplied export; validate against UW First Destination Survey documentation.",
        },
        "charts": {
            "by_degree_type": {
                "type": "bar",
                "title": "Next step / credential mix (from UW export CSV)",
                "data": data,
            },
        },
    }

    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
