#!/usr/bin/env python3
"""
Fetch OpenAlex institution stats for UW–Madison and Big Ten–style peers.
Output: frontend/public/data/research_openalex.json (TabBundle-style charts).

Polite use: https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "frontend" / "public" / "data" / "research_openalex.json"

# Resolved OpenAlex institution IDs (education main campus).
INSTITUTIONS: list[tuple[str, str]] = [
    ("UW–Madison", "I135310074"),
    ("U of Minnesota", "I130238516"),
    ("U of Michigan", "I27837315"),
    ("UIUC", "I157725225"),
    ("Ohio State", "I52357470"),
    ("Penn State", "I130769515"),
]

# Used when OpenAlex is unreachable (offline / SSL issues).
FALLBACK_ROWS: list[dict] = [
    {"label": "UW–Madison", "works_count": 241000, "cited_by_count": 4200000},
    {"label": "U of Minnesota", "works_count": 198000, "cited_by_count": 3100000},
    {"label": "U of Michigan", "works_count": 312000, "cited_by_count": 6100000},
    {"label": "UIUC", "works_count": 225000, "cited_by_count": 3800000},
    {"label": "Ohio State", "works_count": 205000, "cited_by_count": 3400000},
    {"label": "Penn State", "works_count": 189000, "cited_by_count": 2900000},
]

UA = "BadgerNet/4.0 (https://github.com/dpark1719/BadgerNet-4.0; research snapshot)"


def fetch_inst(openalex_id_short: str) -> dict:
    url = f"https://api.openalex.org/institutions/{openalex_id_short}"
    req = Request(url, headers={"User-Agent": UA})
    with urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    from datetime import datetime, timezone

    rows = []
    for label, oid in INSTITUTIONS:
        try:
            doc = fetch_inst(oid)
            time.sleep(0.15)
        except Exception as e:  # noqa: BLE001
            print(f"warn: {label} ({oid}): {e}")
            continue
        rows.append(
            {
                "label": label,
                "works_count": int(doc.get("works_count") or 0),
                "cited_by_count": int(doc.get("cited_by_count") or 0),
                "openalex_id": doc.get("id", ""),
            }
        )

    source = "openalex"
    methodology = (
        "Institution-level counts from OpenAlex API (works_count, cited_by_count). "
        "Peers are R1-style public flagships for comparison — not an official NCAA or "
        "Big Ten designation. Medical-center satellites may inflate some campuses."
    )
    disclaimer = (
        "Bibliometric snapshot, not IPEDS research dollars (HERD). "
        "Counts change as OpenAlex indexes new works."
    )

    if not rows:
        rows = [dict(r) for r in FALLBACK_ROWS]
        source = "openalex_static_fallback"
        methodology = (
            "Illustrative peer-scale numbers for UI when the OpenAlex API cannot be reached "
            "(SSL, offline, or rate limits). Re-run this script on a machine with working TLS "
            "to pull live OpenAlex institution entities."
        )
        disclaimer = (
            "Fallback values are order-of-magnitude placeholders — not live OpenAlex pulls."
        )

    payload = {
        "meta": {
            "project": "BadgerNet 4.0",
            "tab": "research_openalex",
            "snapshot_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "degree_level": "all",
            "source": source,
            "source_url": "https://openalex.org/",
            "methodology": methodology,
            "disclaimer": disclaimer,
        },
        "charts": {
            "works_count_peer_bar": {
                "type": "bar",
                "title": "Indexed works (OpenAlex institution entity)",
                "data": [{"label": r["label"], "value": r["works_count"]} for r in rows],
            },
            "cited_by_count_peer_bar": {
                "type": "bar",
                "title": "Cited-by count (OpenAlex institution aggregate)",
                "data": [{"label": r["label"], "value": r["cited_by_count"]} for r in rows],
            },
            "works_share_uw": {
                "type": "metric",
                "title": "UW–Madison share of peer group — indexed works",
                "value": round(
                    100
                    * next(r for r in rows if r["label"] == "UW–Madison")["works_count"]
                    / sum(r["works_count"] for r in rows),
                    2,
                ),
                "unit": "percent",
            },
            "citations_per_work_proxy": {
                "type": "bar",
                "title": "Citations per work (cited_by_count / works_count)",
                "data": [
                    {
                        "label": r["label"],
                        "value": round(r["cited_by_count"] / max(r["works_count"], 1), 2),
                    }
                    for r in rows
                ],
            },
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(rows)} institutions)")


if __name__ == "__main__":
    main()
