#!/usr/bin/env python3
"""
Post-grad / first-destination style metrics from **local** UW exports.

UW–Madison publishes First Destination Survey primarily via Tableau / web pages
(e.g. https://data.wisc.edu/first-destination-survey/), not a single stable PDF.

CSV formats (header row required):

**Credential mix** (existing):
  credential_type,count   OR   label,count   OR   type,count

**Grad / PhD program destinations** (institution-level):
  institution,count   OR   school,count   OR   graduate_school,count

**Combined file** — optional `kind` column:
  kind,label,count
  credential,Master's,890
  institution,UW–Madison,420

If a row has both `institution` and `credential_type`, institution wins for that row.

Usage:
  python ingest_uw_postgrad.py --csv /path/to/fds_export.csv
  python ingest_uw_postgrad.py --csv institutions.csv --merge   # keep existing charts (e.g. trends)

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


def _norm_row(row: dict) -> dict[str, str]:
    return {k.lower().strip(): (v or "").strip() for k, v in row.items() if k}


def _parse_int(val: str | None) -> int | None:
    if val is None or val == "":
        return None
    try:
        return int(float(val))
    except ValueError:
        return None


def parse_csv(path: Path) -> tuple[dict[str, int], dict[str, int]]:
    """Returns (credential_counts, institution_counts)."""
    cred: dict[str, int] = defaultdict(int)
    inst: dict[str, int] = defaultdict(int)

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            keys = _norm_row(row)
            kind = (keys.get("kind") or "").lower()
            val = _parse_int(keys.get("count") or keys.get("value"))
            if val is None:
                continue

            inst_label = (
                keys.get("institution")
                or keys.get("school")
                or keys.get("graduate_school")
                or keys.get("university")
                or keys.get("phd_program")
                or keys.get("grad_program")
            )
            cred_label = (
                keys.get("credential_type")
                or keys.get("credential")
                or keys.get("degree_type")
            )
            generic = keys.get("label") or keys.get("type")

            if kind in ("institution", "school", "graduate", "grad", "phd"):
                lab = inst_label or generic
                if lab:
                    inst[lab] += val
                continue
            if kind in ("credential", "degree", "type"):
                lab = cred_label or generic
                if lab:
                    cred[lab] += val
                continue

            if inst_label:
                inst[inst_label] += val
            elif cred_label:
                cred[cred_label] += val
            elif generic:
                cred[generic] += val

    return dict(cred), dict(inst)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", type=Path, help="Local CSV from UW FDS / outcomes export")
    ap.add_argument(
        "--merge",
        action="store_true",
        help="Read existing postgrad.json and only replace charts built from this CSV",
    )
    args = ap.parse_args()

    if not args.csv or not args.csv.is_file():
        print(__doc__)
        print("\nOfficial starting points:")
        print("  https://data.wisc.edu/first-destination-survey/")
        print("  https://careers.wisc.edu/first-destination-survey/")
        return

    cred, inst = parse_csv(args.csv)
    if not cred and not inst:
        print(
            "No numeric rows parsed. Expected credential_type,count and/or institution,count "
            "(see docstring)."
        )
        return

    prev: dict | None = None
    if args.merge and OUT.is_file():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            prev = None

    charts: dict = dict((prev or {}).get("charts") or {})

    if cred:
        data = [{"label": k, "value": v} for k, v in sorted(cred.items(), key=lambda x: -x[1])]
        charts["by_degree_type"] = {
            "type": "bar",
            "title": "Next step / credential mix (from UW export CSV)",
            "data": data,
        }
    if inst:
        data_i = [{"label": k, "value": v} for k, v in sorted(inst.items(), key=lambda x: -x[1])]
        charts["grad_phd_destinations"] = {
            "type": "bar",
            "title": "Further study — grad school / PhD program (from UW export CSV)",
            "data": data_i,
        }

    if not charts:
        print("Nothing to write after parse.")
        return

    meta = {
        "project": "BadgerNet 4.0",
        "tab": "postgrad",
        "snapshot_date": datetime.now().strftime("%Y-%m-%d"),
        "degree_level": "all",
        "source": "uw_survey",
        "source_url": "https://data.wisc.edu/first-destination-survey/",
        "methodology": f"Imported from local CSV: {args.csv.name}. Verify cohort and definitions against UW.",
        "disclaimer": "User-supplied export; validate against UW First Destination Survey documentation.",
    }
    if prev and prev.get("meta"):
        old = prev["meta"]
        for k in ("academic_year", "disclaimer", "source", "source_url"):
            if k in old and old[k]:
                meta[k] = old[k]
        extra = f" Merged chart(s) from {args.csv.name}."
        meta["methodology"] = (old.get("methodology") or meta["methodology"]).rstrip() + extra

    payload = {"meta": meta, "charts": charts}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} chart keys: {', '.join(sorted(charts))}")


if __name__ == "__main__":
    main()
