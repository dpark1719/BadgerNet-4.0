#!/usr/bin/env python3
"""Emit frontend/public/data/sources_index.json — catalog of tab JSON bundles."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "frontend" / "public" / "data"
OUT = DATA / "sources_index.json"

# Tab id -> relative path under public/data (no leading slash; empty = no JSON file)
BUNDLES: list[tuple[str, str, str]] = [
    ("data_sources", "", "Data catalog (this page)"),
    ("industry", "industry.json", "Industry"),
    ("postgrad", "postgrad.json", "Post-grad education"),
    ("international", "international.json", "International outcomes"),
    ("world_map", "map_destinations.json", "World map (overlay)"),
    ("visualize", "vizualive.json", "Visualize"),
    ("notable_alumni", "notable.json", "Notable alumni"),
    ("origins_undergrad", "origins_undergrad.json", "Origins — Undergraduate"),
    ("origins_graduate", "origins_graduate.json", "Origins — Graduate"),
    ("origins_doctorate", "origins_doctorate.json", "Origins — Doctorate"),
    ("outcomes_scorecard", "outcomes_scorecard.json", "Peer outcomes (Scorecard)"),
    ("research_openalex", "research_openalex.json", "Research footprint (OpenAlex)"),
    ("rankings", "rankings.json", "Rankings (hub)"),
]


def main() -> None:
    rows = []
    for tab_id, rel, label in BUNDLES:
        path = DATA / rel if rel else Path()
        snap = source = methodology = disclaimer = None
        if not rel:
            methodology = (
                "Self-index for this app: each row points to a JSON bundle (or special tab). "
                "Use URL query `?tab=` and `?years=` to deep-link views."
            )
            file_exists = True
        elif path.exists():
            file_exists = True
            try:
                doc = json.loads(path.read_text(encoding="utf-8"))
                meta = doc.get("meta") or {}
                snap = meta.get("snapshot_date")
                source = meta.get("source")
                methodology = meta.get("methodology")
                disclaimer = meta.get("disclaimer")
            except (json.JSONDecodeError, OSError):
                pass
        else:
            file_exists = False
        rows.append(
            {
                "tab_id": tab_id,
                "label": label,
                "relative_path": rel,
                "snapshot_date": snap,
                "source": source,
                "methodology": methodology,
                "disclaimer": disclaimer,
                "file_exists": file_exists,
            }
        )

    payload = {
        "snapshot_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "bundles": rows,
        "notes": [
            "Major slices live under data/majors/*.json (Industry tab only).",
            "Run fetch_wikidata_notable.py to refresh notable.json.",
            "IPEDS builders: build_origins_ipeds.py, build_international_proxy.py.",
            "Rankings: run backend/scripts/harvest_rankings.py (Wikidata + IPEDS).",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(rows)} bundles)")


if __name__ == "__main__":
    main()
