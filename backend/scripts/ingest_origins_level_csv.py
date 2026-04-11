#!/usr/bin/env python3
"""
Populate origins_graduate.json or origins_doctorate.json from **local** CSVs.

Official IPEDS EF…C tables used for freshmen do not substitute for graduate /
doctoral geography. Typical inputs:

- Columns pasted from **UW Common Data Set** Section B (Excel), or
- UW / IPEDS **Fall Enrollment** extracts you export with state / country columns.

CSV format (one file can hold both series):

  kind,label,value

- kind: `state` (US state or region name) or `country`
- label: state name or country name
- value: integer count

Alternatively use separate files:

  --states-csv  with columns label,value  (or state,count)
  --countries-csv  with columns label,value  (or country,count)

Outputs:
  --level graduate   -> frontend/public/data/origins_graduate.json
  --level doctorate  -> frontend/public/data/origins_doctorate.json

CDS downloads (human step): https://data.wisc.edu/common-data-set-and-rankings/
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TAB_FOR = {
    "graduate": "origins_graduate",
    "doctorate": "origins_doctorate",
}

OUT_FOR = {
    "graduate": ROOT / "frontend" / "public" / "data" / "origins_graduate.json",
    "doctorate": ROOT / "frontend" / "public" / "data" / "origins_doctorate.json",
}


def _read_label_value(path: Path) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            keys = {k.lower().strip(): v for k, v in row.items() if k}
            lab = (
                keys.get("label")
                or keys.get("state")
                or keys.get("country")
                or keys.get("name")
            )
            val = keys.get("value") or keys.get("count")
            if not lab or val is None:
                continue
            try:
                n = int(float(str(val).strip()))
            except ValueError:
                continue
            s = str(lab).strip()
            if s:
                out.append((s, n))
    return out


def _read_combined(path: Path) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    states: list[tuple[str, int]] = []
    countries: list[tuple[str, int]] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            keys = {k.lower().strip(): v for k, v in row.items() if k}
            kind = (keys.get("kind") or keys.get("series") or "").strip().lower()
            lab = (
                keys.get("label")
                or keys.get("state")
                or keys.get("country")
            )
            val = keys.get("value") or keys.get("count")
            if not kind or not lab or val is None:
                continue
            try:
                n = int(float(str(val).strip()))
            except ValueError:
                continue
            s = str(lab).strip()
            if not s:
                continue
            if kind in ("state", "us", "us_state", "states"):
                states.append((s, n))
            elif kind in ("country", "countries", "intl", "international"):
                countries.append((s, n))
    return states, countries


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--level", choices=("graduate", "doctorate"), required=True)
    ap.add_argument("--csv", type=Path, help="Combined CSV with kind,label,value")
    ap.add_argument("--states-csv", type=Path)
    ap.add_argument("--countries-csv", type=Path)
    ap.add_argument("--academic-year", type=str, default="", help="e.g. 2023-24")
    ap.add_argument(
        "--methodology",
        type=str,
        default="",
        help="Override meta.methodology (default describes CSV ingest)",
    )
    args = ap.parse_args()

    states: list[tuple[str, int]] = []
    countries: list[tuple[str, int]] = []

    if args.csv:
        s, c = _read_combined(args.csv)
        states, countries = s, c
    if args.states_csv:
        states = _read_label_value(args.states_csv)
    if args.countries_csv:
        countries = _read_label_value(args.countries_csv)

    if not states and not countries:
        raise SystemExit("Provide --csv (kind,label,value) and/or --states-csv / --countries-csv")

    for name, pairs in (("states", states), ("countries", countries)):
        pairs.sort(key=lambda x: -x[1])

    level_title = "Grad" if args.level == "graduate" else "PhD"
    charts: dict = {}
    if states:
        charts["us_states"] = {
            "type": "bar",
            "title": f"US home state / region — enrolled ({level_title}, user CSV)",
            "data": [{"label": a, "value": b} for a, b in states],
        }
    if countries:
        charts["countries"] = {
            "type": "bar",
            "title": f"Country of origin — international enrolled ({level_title}, user CSV)",
            "data": [{"label": a, "value": b} for a, b in countries],
        }

    ay = args.academic_year.strip() or "—"
    meth = args.methodology.strip() or (
        f"Imported from local CSV for {args.level} level. "
        "Verify cohort (all grads vs new admits) against UW CDS / IPEDS definitions."
    )

    deg = "graduate" if args.level == "graduate" else "doctorate"
    payload = {
        "meta": {
            "project": "BadgerNet 4.0",
            "snapshot_date": datetime.now().strftime("%Y-%m-%d"),
            "academic_year": ay,
            "tab": TAB_FOR[args.level],
            "degree_level": deg,
            "source": "uw_cds",
            "source_url": "https://data.wisc.edu/common-data-set-and-rankings/",
            "methodology": meth,
            "disclaimer": "User-supplied extract — not an automated IPEDS pull. Do not mix cohorts across files.",
        },
        "charts": charts,
    }

    out = OUT_FOR[args.level]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out.relative_to(ROOT)} ({len(states)} state rows, {len(countries)} country rows)")


if __name__ == "__main__":
    main()
