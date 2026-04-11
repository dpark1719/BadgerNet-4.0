#!/usr/bin/env python3
"""
Optional: pull a few institution-level fields from College Scorecard API for
context (not employer/industry breakdowns — those are not in Scorecard).

Register for a free key: https://api.data.gov/signup/
Set env: COLLEGE_SCORECARD_API_KEY

Writes a small JSON fragment to data/raw/scorecard_UW.json for reference;
does not replace frontend bundles by itself.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "raw" / "scorecard_UW.json"

# UW–Madison OPEID 00389500 → sometimes searched by id
API = "https://api.data.gov/ed/collegescorecard/v1/schools.json"


def main() -> None:
    key = os.environ.get("COLLEGE_SCORECARD_API_KEY", "").strip()
    if not key:
        print("Set COLLEGE_SCORECARD_API_KEY to run this script.")
        return

    params = {
        "api_key": key,
        "school.name": "University of Wisconsin-Madison",
        "fields": ",".join(
            [
                "id",
                "school.name",
                "school.city",
                "latest.student.size",
                "latest.completion.rate_suppressed.overall",
                "latest.earnings.10_yrs_after_entry.median",
            ]
        ),
    }
    r = requests.get(API, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
