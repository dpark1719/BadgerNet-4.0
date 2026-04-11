#!/usr/bin/env python3
"""
Convert **reviewed** LinkedIn (or other) aggregate CSV exports into majors/*.json.

No scraping here — you produce CSV from your harvest / manual filters.

CSV columns (header row required):
  major_id, chart_key, type, title, label, value, extra_json

- major_id: matches majors/index.json id (e.g. computer_science)
- chart_key: e.g. top_employers, by_industry, career_flow (sankey uses multiple rows — see below)
- type: bar | metric | trend | sankey_node | sankey_link
- title: chart title (repeat per row for same chart_key — last wins)
- label: bar label, metric ignored, trend series key, sankey node id or link source
- value: number; for sankey_link use target in extra_json as {"target":"x"}

For sankey:
  sankey_node rows: type=sankey_node, label=display label, value unused, extra_json={"id":"node_id"}
  sankey_link rows: type=sankey_link, label=source_id, value=flow, extra_json={"target":"target_id"}

Example minimal top employers:
  major_id,chart_key,type,title,label,value,extra_json
  computer_science,top_employers,bar,Top employers,Google,50,
  computer_science,top_employers,bar,Top employers,Meta,30,
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAJORS_DIR = ROOT / "frontend" / "public" / "data" / "majors"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path", type=Path)
    args = ap.parse_args()

    if not args.csv_path.is_file():
        raise SystemExit(f"Missing file: {args.csv_path}")

    by_major: dict[str, dict] = defaultdict(lambda: {"charts": {}})

    with args.csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            mid = (row.get("major_id") or "").strip()
            if not mid:
                continue
            ck = (row.get("chart_key") or "").strip()
            typ = (row.get("type") or "bar").strip().lower()
            title = (row.get("title") or "").strip()
            label = (row.get("label") or "").strip()
            extra = (row.get("extra_json") or "").strip()
            try:
                val = float(row.get("value") or 0)
            except ValueError:
                val = 0
            extra_obj = json.loads(extra) if extra else {}

            slot = by_major[mid]["charts"].setdefault(
                ck,
                {"type": "bar", "title": title, "data": []},
            )
            if title:
                slot["title"] = title

            if typ == "bar":
                slot["type"] = "bar"
                slot.setdefault("data", []).append({"label": label, "value": int(val)})
            elif typ == "metric":
                slot["type"] = "metric"
                slot["title"] = title
                slot["value"] = val
                slot["unit"] = extra_obj.get("unit", "percent")
            elif typ == "sankey_node":
                slot["type"] = "sankey"
                slot.setdefault("nodes", [])
                nid = extra_obj.get("id") or label
                slot["nodes"].append({"id": nid, "label": label or nid})
            elif typ == "sankey_link":
                slot["type"] = "sankey"
                slot.setdefault("links", [])
                tgt = extra_obj.get("target", "")
                slot["links"].append({"source": label, "target": tgt, "value": int(val)})

    common_meta = {
        "project": "BadgerNet 4.0",
        "snapshot_date": datetime.now().strftime("%Y-%m-%d"),
        "degree_level": "undergraduate",
        "source": "linkedin",
        "methodology": f"Built from aggregate CSV {args.csv_path.name}; document filters separately.",
        "disclaimer": "LinkedIn-visible aggregates; biased and incomplete.",
    }

    MAJORS_DIR.mkdir(parents=True, exist_ok=True)
    for mid, blob in by_major.items():
        for ck, spec in blob["charts"].items():
            if spec.get("type") == "sankey":
                spec.setdefault("nodes", [])
                spec.setdefault("links", [])
        out = {
            "meta": {
                **common_meta,
                "tab": "industry",
                "major_id": mid,
            },
            "charts": blob["charts"],
        }
        dest = MAJORS_DIR / f"{mid}.json"
        dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
