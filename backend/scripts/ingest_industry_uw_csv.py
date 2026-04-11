#!/usr/bin/env python3
"""
Import **all-majors** industry / employer bars from a local CSV into industry.json.

Expected columns:
  chart_key,label,value

- chart_key: e.g. `by_industry`, `top_employers` (must match keys the UI already uses)
- label: sector or employer name
- value: numeric count or weight

Merges into existing industry.json: **replaces** only the chart keys present in
the CSV; leaves other charts (e.g. trends) unchanged unless you include rows
for those keys.

Source examples: UW career outcomes / employer tables exported to CSV,
LinkedIn Talent Insights roll-up you saved locally — not per-profile scrapes.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "frontend" / "public" / "data" / "industry.json"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--source-url",
        type=str,
        default="https://careers.wisc.edu/",
        help="Citation URL written to meta.source_url",
    )
    args = ap.parse_args()

    if not args.csv.is_file():
        raise SystemExit(f"Missing: {args.csv}")

    by_chart: dict[str, list[tuple[str, int]]] = defaultdict(list)
    titles: dict[str, str] = {}

    with args.csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            keys = {k.lower().strip(): v for k, v in row.items() if k}
            ck = (keys.get("chart_key") or "").strip()
            label = (keys.get("label") or keys.get("name") or "").strip()
            title = (keys.get("title") or "").strip()
            val_s = keys.get("value") or keys.get("count")
            if not ck or not label or val_s is None:
                continue
            try:
                v = int(float(str(val_s).strip()))
            except ValueError:
                continue
            by_chart[ck].append((label, v))
            if title:
                titles[ck] = title

    if not by_chart:
        raise SystemExit("No rows; expected chart_key,label,value")

    if args.out.is_file():
        payload = json.loads(args.out.read_text(encoding="utf-8"))
    else:
        payload = {"meta": {}, "charts": {}}

    meta = payload.setdefault("meta", {})
    prev_meth = (meta.get("methodology") or "").strip()
    snap = datetime.now().strftime("%Y-%m-%d")
    new_meth = f"Charts {sorted(by_chart.keys())} updated from CSV `{args.csv.name}`."
    meta.update(
        {
            "project": "BadgerNet 4.0",
            "snapshot_date": snap,
            "tab": "industry",
            "degree_level": "all",
            "source": "uw_survey",
            "source_url": args.source_url,
            "methodology": (prev_meth + " " + new_meth).strip() if prev_meth else new_meth,
            "disclaimer": meta.get("disclaimer")
            or "User-supplied export — validate definitions against the cited UW or vendor documentation.",
        }
    )

    charts = payload.setdefault("charts", {})
    for ck, pairs in by_chart.items():
        pairs.sort(key=lambda x: -x[1])
        title = titles.get(ck) or ck.replace("_", " ").title()
        charts[ck] = {
            "type": "bar",
            "title": title,
            "data": [{"label": a, "value": b} for a, b in pairs],
        }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out.relative_to(ROOT)} chart keys: {', '.join(sorted(by_chart))}")


if __name__ == "__main__":
    main()
