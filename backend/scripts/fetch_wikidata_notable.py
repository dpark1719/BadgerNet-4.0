#!/usr/bin/env python3
"""
Fetch notable alumni seeds from Wikidata (people with "educated at"
University of Wisconsin–Madison, Q838330).

Enriches each row with:
- photo_url: Wikidata P18 (Commons) or English Wikipedia lead thumbnail
- achievement_image_url / achievement_label: inferred from role text + Wikipedia summary

Output: frontend/public/data/notable.json
Requires: requests

Respect Wikidata User-Agent policy:
https://wikimediafoundation.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend.lib.notable_enrichment import (  # noqa: E402
    commons_image_thumb,
    fetch_wikipedia_summary,
    infer_achievement_from_text,
    photo_url_from_summary,
    short_bio_from_summary,
)

OUT = ROOT / "frontend" / "public" / "data" / "notable.json"

UW_QID = "Q838330"
ENDPOINT = "https://query.wikidata.org/sparql"

SPARQL = """
SELECT ?person ?personLabel ?wp ?image WHERE {
  ?person wdt:P69 wd:Q838330 .
  OPTIONAL {
    ?wp schema:about ?person .
    ?wp schema:isPartOf <https://en.wikipedia.org/> .
  }
  OPTIONAL { ?person wdt:P18 ?image . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
LIMIT 100
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=80, help="Max rows (Wikidata query LIMIT)")
    ap.add_argument(
        "--thumb-delay",
        type=float,
        default=0.06,
        help="Seconds between Wikipedia API calls (be polite)",
    )
    ap.add_argument(
        "--skip-enrich",
        action="store_true",
        help="Wikidata only; no Wikipedia thumbnail / achievement calls",
    )
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

    session = requests.Session()
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
        img_binding = b.get("image", {}).get("value", "").strip()
        wd_photo = commons_image_thumb(img_binding, 160) if img_binding else None

        fallback_role = "Notable person (Wikidata: educated at UW–Madison)"
        role_title = fallback_role
        organization = "—"
        summary = None
        photo_url = wd_photo
        ach_url = None
        ach_label = None

        if not args.skip_enrich:
            summary = fetch_wikipedia_summary(session, wp, pause_s=args.thumb_delay)
            if not photo_url and summary:
                photo_url = photo_url_from_summary(summary)
            if summary:
                bio = short_bio_from_summary(summary)
                if bio:
                    role_title = bio
            ach_url, ach_label = infer_achievement_from_text(
                role_title, organization, summary
            )

        row: dict = {
            "name": name,
            "role_title": role_title,
            "organization": organization,
            "notability": "widely_cited",
            "source_url": wp,
            "source_type": "wikipedia",
        }
        if photo_url:
            row["photo_url"] = photo_url
        if ach_url and ach_label:
            row["achievement_image_url"] = ach_url
            row["achievement_label"] = ach_label
        entries.append(row)

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
                "with an English Wikipedia sitelink. Optional P18 image; Wikipedia REST summary for "
                "missing photos and for achievement badges (Nobel, founder, etc.) inferred from lead text. "
                "Not vetted for graduation or degree type; verify each source."
            ),
            "disclaimer": (
                "Automated list from Wikidata — not an official UW ranking, incomplete, and may include "
                "faculty or short-term attendees. Photos are Commons/Wikipedia-sourced; verify licensing for reuse."
            ),
        },
        "entries": entries[: args.limit],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with_photo = sum(1 for e in payload["entries"] if e.get("photo_url"))
    with_badge = sum(1 for e in payload["entries"] if e.get("achievement_image_url"))
    print(
        f"Wrote {OUT.relative_to(ROOT)} with {len(payload['entries'])} entries "
        f"({with_photo} with photo_url, {with_badge} with achievement badge)"
    )


if __name__ == "__main__":
    main()
