#!/usr/bin/env python3
"""
Merge **user-supplied** country-level aggregates into international.json.

Use this for LinkedIn (or other) **roll-up exports** you created with explicit
filters — not raw profiles. Typical CSV columns: country,count
(alternatively: label,value).

Workflow:
  1. python backend/scripts/build_international_proxy.py   # IPEDS context bar
  2. python backend/scripts/ingest_international_destinations_csv.py \\
       --csv data/raw/my_intl_destinations.csv \\
       [--fingerprint "school=UW-Madison; cohort=…"]

Updates frontend/public/data/international.json in place: adds chart key
`aggregate_destination_proxy` and sets meta.source to mixed when combined
with IPEDS.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE = ROOT / "frontend" / "public" / "data" / "international.json"


def _fingerprint_from_rows(rows: list[tuple[str, int]]) -> str:
    blob = "|".join(f"{a}:{b}" for a, b in sorted(rows))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", type=Path, required=True, help="country,count (or label,value)")
    ap.add_argument("--base", type=Path, default=DEFAULT_BASE, help="Existing international.json")
    ap.add_argument(
        "--fingerprint",
        type=str,
        default="",
        help="Human-readable filter summary; default: hash of sorted rows",
    )
    ap.add_argument(
        "--title",
        type=str,
        default="Post-UW destination — aggregate proxy (user CSV)",
        help="Chart title",
    )
    args = ap.parse_args()

    if not args.csv.is_file():
        raise SystemExit(f"Missing CSV: {args.csv}")

    rows: list[tuple[str, int]] = []
    with args.csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for raw in reader:
            keys = {k.lower().strip(): v for k, v in raw.items() if k}
            label = (
                keys.get("country")
                or keys.get("label")
                or keys.get("destination")
                or keys.get("region")
            )
            val = keys.get("count") or keys.get("value") or keys.get("n")
            if not label or val is None:
                continue
            try:
                n = int(float(str(val).strip()))
            except ValueError:
                continue
            label = str(label).strip()
            if label:
                rows.append((label, n))

    if not rows:
        raise SystemExit("No numeric rows parsed; expected columns like country,count")

    rows.sort(key=lambda x: -x[1])
    fp = args.fingerprint.strip() or _fingerprint_from_rows(rows)

    if args.base.is_file():
        payload = json.loads(args.base.read_text(encoding="utf-8"))
    else:
        payload = {
            "meta": {
                "project": "BadgerNet 4.0",
                "tab": "international_outcomes",
                "snapshot_date": datetime.now().strftime("%Y-%m-%d"),
                "degree_level": "all",
                "source": "linkedin_aggregate",
                "source_url": None,
                "methodology": "No IPEDS base file found; proxy chart only.",
                "disclaimer": "User-supplied aggregate — not an official UW census.",
            },
            "charts": {},
        }

    meta = payload.setdefault("meta", {})
    meta["snapshot_date"] = datetime.now().strftime("%Y-%m-%d")
    charts_existing = payload.get("charts") or {}
    if "ipeds_foreign_context" in charts_existing:
        meta["source"] = "mixed"
    else:
        meta["source"] = "linkedin_aggregate"

    extra = (
        f" Destination proxy from local CSV `{args.csv.name}`: counts by country/region. "
        f"Filter fingerprint: {fp}. "
        "This is not a complete census of alumni; coverage follows the export tool and filters."
    )
    meta["methodology"] = (meta.get("methodology") or "").rstrip() + extra
    meta["filter_fingerprint"] = fp
    disc = (
        "The chart `aggregate_destination_proxy` reflects a user-defined aggregate export "
        "(e.g. LinkedIn Talent Insights roll-up), not verified migration records. "
        "Do not equate with visa or tax residency."
    )
    if meta.get("disclaimer"):
        meta["disclaimer"] = meta["disclaimer"].rstrip() + " " + disc
    else:
        meta["disclaimer"] = disc

    charts = payload.setdefault("charts", {})
    charts["aggregate_destination_proxy"] = {
        "type": "bar",
        "title": args.title,
        "data": [{"label": lab, "value": n} for lab, n in rows],
    }

    args.base.parent.mkdir(parents=True, exist_ok=True)
    args.base.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.base.relative_to(ROOT)} (+ aggregate_destination_proxy, n={len(rows)})")


if __name__ == "__main__":
    main()
