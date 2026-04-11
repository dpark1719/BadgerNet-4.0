#!/usr/bin/env python3
"""
Append manually curated notable entries to notable.json (e.g. after Wikidata).

Manual file: JSON object `{ "entries": [ { ... same fields as NotableEntry ... } ] }`
See frontend types / DATA_CONTRACT.md for shape (name, role_title, organization,
notability, source_url, source_type, optional year).

Dedupes by normalized name (case-insensitive); manual entries **skip** if name
already present. Sets meta.source to `mixed` when merging.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE = ROOT / "frontend" / "public" / "data" / "notable.json"


def norm(s: str) -> str:
    return s.lower().strip()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manual", type=Path, required=True, help="JSON with entries[]")
    ap.add_argument("--base", type=Path, default=DEFAULT_BASE)
    args = ap.parse_args()

    if not args.manual.is_file():
        raise SystemExit(f"Missing manual file: {args.manual}")

    manual = json.loads(args.manual.read_text(encoding="utf-8"))
    extra = manual.get("entries") if isinstance(manual, dict) else None
    if not isinstance(extra, list):
        raise SystemExit("manual JSON must be { \"entries\": [ ... ] }")

    if args.base.is_file():
        payload = json.loads(args.base.read_text(encoding="utf-8"))
    else:
        payload = {"meta": {}, "entries": []}

    entries = payload.setdefault("entries", [])
    seen = {norm(e["name"]) for e in entries if isinstance(e, dict) and e.get("name")}

    added = 0
    for e in extra:
        if not isinstance(e, dict):
            continue
        name = e.get("name")
        if not name or norm(name) in seen:
            continue
        required = ("role_title", "organization", "notability", "source_url", "source_type")
        if not all(e.get(k) for k in required):
            print(f"Skip incomplete entry: {name!r}")
            continue
        entries.append(e)
        seen.add(norm(name))
        added += 1

    meta = payload.setdefault("meta", {})
    meta["snapshot_date"] = datetime.now().strftime("%Y-%m-%d")
    if meta.get("source") and meta["source"] != "manual":
        meta["source"] = "mixed"
    extra_m = f" Merged {added} manual entries from `{args.manual.name}`."
    meta["methodology"] = (meta.get("methodology") or "").rstrip() + extra_m

    args.base.parent.mkdir(parents=True, exist_ok=True)
    args.base.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.base.relative_to(ROOT)} (+{added} entries, total {len(entries)})")


if __name__ == "__main__":
    main()
