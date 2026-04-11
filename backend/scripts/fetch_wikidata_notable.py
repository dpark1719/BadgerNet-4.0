#!/usr/bin/env python3
"""
Fetch notable alumni seeds from Wikidata (people with "educated at"
University of Wisconsin–Madison, Q838330).

Output: frontend/public/data/notable.json
Requires: requests

Respect Wikidata User-Agent policy:
https://wikimediafoundation.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "frontend" / "public" / "data" / "notable.json"

UW_QID = "Q838330"
ENDPOINT = "https://query.wikidata.org/sparql"

SPARQL = """
SELECT ?person ?personLabel ?wp WHERE {
  ?person wdt:P69 wd:Q838330 .
  OPTIONAL {
    ?wp schema:about ?person .
    ?wp schema:isPartOf <https://en.wikipedia.org/> .
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 100
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=80, help="Max rows (Wikidata query LIMIT)")
    args = ap.parse_args()

    q = SPARQL.replace("LIMIT 100", f"LIMIT {args.limit}")
    headers = {
        "User-Agent": "BadgerNet4/1.0 (https://github.com/dpark1719/BadgerNet-4.0; data pipeline)",
        "Accept": "application/sparql-results+json",
    }
    r = requests.get(
        ENDPOINT,
        params={"query": q, "format": "json"},
        headers=headers,
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    bindings = data.get("results", {}).get("bindings", [])

    entries = []
    seen_uri = set()
    for b in bindings:
        uri = b.get("person", {}).get("value", "")
        if uri in seen_uri:
            continue
        seen_uri.add(uri)
        name = b.get("personLabel", {}).get("value", "")
        if not name:
            continue
        wp = b.get("wp", {}).get("value", "")
        if not wp:
            continue
        entries.append(
            {
                "name": name,
                "role_title": "Notable person (Wikidata: educated at UW–Madison)",
                "organization": "—",
                "notability": "widely_cited",
                "source_url": wp,
                "source_type": "wikipedia",
            }
        )

    payload = {
        "meta": {
            "project": "BadgerNet 4.0",
            "tab": "notable_alumni",
            "snapshot_date": datetime.now().strftime("%Y-%m-%d"),
            "degree_level": "all",
            "source": "wikidata",
            "source_url": "https://www.wikidata.org/",
            "methodology": (
                f"SPARQL against Wikidata: entities with P69 (educated at) = {UW_QID} (UW–Madison), "
                "with an English Wikipedia sitelink. Not vetted for graduation or degree type; verify each source."
            ),
            "disclaimer": (
                "Automated list from Wikidata — not an official UW ranking, incomplete, and may include "
                "faculty or short-term attendees. Every row links to Wikipedia for verification."
            ),
        },
        "entries": entries[: args.limit],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} with {len(payload['entries'])} entries")


if __name__ == "__main__":
    main()
