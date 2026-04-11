#!/usr/bin/env python3
"""
Convert **reviewed** LinkedIn (or other) aggregate CSV exports into majors/*.json.

No scraping here — you produce CSV from your harvest / manual filters.

CSV columns (header row required):
  major_id, chart_key, type, title, label, value, extra_json
  Optional: major_label, major_cip (first non-empty per major_id → slice meta for index sync)

- major_id: filename stem for majors/{major_id}.json (e.g. computer_science)
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
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAJORS_DIR = ROOT / "frontend" / "public" / "data" / "majors"
sys.path.insert(0, str(ROOT))
from backend.lib.majors_index import sync_majors_index  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path", type=Path)
    args = ap.parse_args()

    if not args.csv_path.is_file():
        raise SystemExit(f"Missing file: {args.csv_path}")

    by_major: dict[str, dict] = defaultdict(lambda: {"charts": {}})
    major_labels: dict[str, str] = {}
    major_cips: dict[str, str] = {}

    with args.csv_path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            mid = (row.get("major_id") or "").strip()
            if not mid:
                continue
            ml = (row.get("major_label") or "").strip()
            if ml and mid not in major_labels:
                major_labels[mid] = ml
            mc = (row.get("major_cip") or "").strip()
            if mc and mid not in major_cips:
                major_cips[mid] = mc
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
        meta_out = {
            **common_meta,
            "tab": "industry",
            "major_id": mid,
        }
        if mid in major_labels:
            meta_out["major_display_name"] = major_labels[mid]
        if mid in major_cips:
            meta_out["major_cip"] = major_cips[mid]
        out = {"meta": meta_out, "charts": blob["charts"]}
        dest = MAJORS_DIR / f"{mid}.json"
        dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {dest.relative_to(ROOT)}")

    sync_majors_index(MAJORS_DIR, verbose=True)


if __name__ == "__main__":
    main()
