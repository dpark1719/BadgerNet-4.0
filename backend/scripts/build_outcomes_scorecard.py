#!/usr/bin/env python3
"""
Build outcomes_scorecard.json: institution-level metrics for UW + peers.

If COLLEGE_SCORECARD_API_KEY is set, pulls live fields from College Scorecard API.
Otherwise writes a labeled static fallback (approximate public figures for UI).

https://collegescorecard.ed.gov/data/api
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "frontend" / "public" / "data" / "outcomes_scorecard.json"

API = "https://api.data.gov/ed/collegescorecard/v1/schools.json"

# unitid, short label (College Scorecard uses school.unit_id in response)
PEERS: list[tuple[int, str]] = [
    (240444, "UW–Madison"),
    (174066, "U of Minnesota"),
    (170976, "U of Michigan"),
    (145637, "UIUC"),
    (204761, "Ohio State"),
    (214739, "Penn State (University Park)"),
]

FIELDS = [
    "school.name",
    "school.unit_id",
    "latest.student.size",
    "latest.completion.rate_suppressed.overall",
    "latest.earnings.10_yrs_after_entry.median",
]

# Static fallback when API unavailable (rounded illustrative values; refresh with API).
FALLBACK_ROWS: list[dict] = [
    {"label": "UW–Madison", "enrollment": 47625, "completion_pct": 86.2, "earn_10yr": 66100},
    {"label": "U of Minnesota", "enrollment": 54303, "completion_pct": 81.4, "earn_10yr": 62800},
    {"label": "U of Michigan", "enrollment": 50422, "completion_pct": 93.0, "earn_10yr": 72000},
    {"label": "UIUC", "enrollment": 56206, "completion_pct": 85.5, "earn_10yr": 68800},
    {"label": "Ohio State", "enrollment": 61244, "completion_pct": 87.0, "earn_10yr": 62000},
    {"label": "Penn State (University Park)", "enrollment": 47361, "completion_pct": 85.8, "earn_10yr": 64000},
]


def fetch_row(api_key: str, unitid: int) -> dict | None:
    params = {
        "api_key": api_key,
        "school.unit_id": unitid,
        "fields": ",".join(FIELDS),
    }
    url = f"{API}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "BadgerNet/4.0 (outcomes ETL)"})
    with urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    results = data.get("results") or []
    if not results:
        return None
    r = results[0]
    name = r.get("school.name") or str(unitid)
    size = r.get("latest.student.size")
    comp = r.get("latest.completion.rate_suppressed.overall")
    earn = r.get("latest.earnings.10_yrs_after_entry.median")
    return {
        "label": name,
        "enrollment": int(size) if size is not None else 0,
        "completion_pct": round(float(comp) * 100, 2) if comp is not None else 0.0,
        "earn_10yr": int(earn) if earn is not None else 0,
    }


def main() -> None:
    from datetime import datetime, timezone

    key = os.environ.get("COLLEGE_SCORECARD_API_KEY", "").strip()
    rows: list[dict] = []
    source = "college_scorecard_api"
    methodology = (
        "Institution-level fields from College Scorecard API: headcount enrollment, "
        "overall completion rate, and median earnings 10 years after entry. "
        "Definitions follow Scorecard documentation; suppression may zero some cells."
    )

    if key:
        for uid, short in PEERS:
            try:
                row = fetch_row(key, uid)
                if row:
                    row["label"] = short
                    rows.append(row)
            except Exception as e:  # noqa: BLE001
                print(f"warn: unitid {uid}: {e}")
    if not rows:
        rows = [dict(r) for r in FALLBACK_ROWS]
        source = "static_fallback"
        methodology = (
            "Illustrative peer table for UI when COLLEGE_SCORECARD_API_KEY is not set. "
            "Numbers are rounded public-style benchmarks — not a live API pull. "
            "Set COLLEGE_SCORECARD_API_KEY and re-run this script for current Scorecard values."
        )

    payload = {
        "meta": {
            "project": "BadgerNet 4.0",
            "tab": "outcomes_scorecard",
            "snapshot_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "degree_level": "all",
            "source": source,
            "source_url": "https://collegescorecard.ed.gov/",
            "methodology": methodology,
            "disclaimer": (
                "Not UW internal career analytics. Earnings reflect institution-level "
                "Scorecard cohorts, not starting salary by major."
            ),
        },
        "charts": {
            "enrollment_peer_bar": {
                "type": "bar",
                "title": "Total student enrollment (Scorecard latest.student.size)",
                "data": [{"label": r["label"], "value": r["enrollment"]} for r in rows],
            },
            "completion_rate_peer_bar": {
                "type": "bar",
                "title": "Overall completion rate (%)",
                "data": [{"label": r["label"], "value": r["completion_pct"]} for r in rows],
            },
            "median_earnings_10yr_peer_bar": {
                "type": "bar",
                "title": "Median earnings 10 years after entry (USD)",
                "data": [{"label": r["label"], "value": r["earn_10yr"]} for r in rows],
            },
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} (source={source}, n={len(rows)})")


if __name__ == "__main__":
    main()
