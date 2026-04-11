#!/usr/bin/env python3
"""
IPEDS → origins JSON (stub).

University of Wisconsin–Madison **IPEDS UnitID** is **240444** (verify on NCES before production).

Planned flow:
1. Download Fall Enrollment or relevant IPEDS CSV from https://nces.ed.gov/ipeds/datacenter/
2. Filter UnitID == 240444, split by level (undergraduate / graduate / doctoral)
3. Map state of residence and country of origin fields to chart bundles per DATA_CONTRACT.md
4. Write ``frontend/public/data/origins_undergrad.json`` (and grad / doctorate) with ``source: ipeds``

This stub prints instructions only; implement when you have downloaded files in ../data/raw/ (gitignored).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    print("BadgerNet — IPEDS origins stub")
    print(f"  Put IPEDS CSV extracts in: {RAW}")
    print("  Target UnitID: 240444 (UW–Madison) — confirm on NCES.")
    print("  Output files: frontend/public/data/origins_undergrad.json, etc.")
    print("  See DATA_CONTRACT.md and generate_sample_data.py for JSON shape.")
    sys.exit(0)


if __name__ == "__main__":
    main()
