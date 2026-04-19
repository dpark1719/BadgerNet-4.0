#!/usr/bin/env python3
"""
Build a single rankings bundle: frontend/public/data/rankings.json

- Institution tables: Wikidata P1352 + P459 for QS World (Q1790510) and ARWU (Q478743).
  **Global** peer set deliberately mixes U.S. and non-U.S. universities so the world view
  is not U.S.-only (earlier versions were mostly U.S. by design of the peer list).
- Sub-sections inside the app: global | us | public | majors (no separate top-level tabs).
- UW majors: IPEDS Completions C2024_A (UNITID 240444); optional data/raw/major_ranks.csv.

Optional publisher probe: npm run harvest:publishers:probe (Playwright; does not merge).
"""

from __future__ import annotations

import csv
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "frontend" / "public" / "data" / "rankings.json"
RAW = ROOT / "data" / "raw" / "ipeds"
OPTIONAL_MAJOR_RANKS = ROOT / "data" / "raw" / "major_ranks.csv"

UNITID = 240444
UA = "BadgerNet/4.0 (https://github.com/dpark1719/BadgerNet-4.0; harvest_rankings)"

QS = "Q1790510"
ARWU = "Q478743"

# Curated peers. `country` is a short display tag (not an ISO authority).
# Global list mixes US public flagships, US privates, and non-US research universities.
PEERS: list[dict[str, Any]] = [
    {"label": "UW–Madison", "qid": "Q838330", "us": True, "public": True, "country": "US"},
    {"label": "U of Michigan", "qid": "Q230492", "us": True, "public": True, "country": "US"},
    {"label": "U of Minnesota", "qid": "Q238101", "us": True, "public": True, "country": "US"},
    {"label": "UIUC", "qid": "Q457281", "us": True, "public": True, "country": "US"},
    {"label": "Ohio State", "qid": "Q309331", "us": True, "public": True, "country": "US"},
    {"label": "Penn State", "qid": "Q739627", "us": True, "public": True, "country": "US"},
    {"label": "MIT", "qid": "Q49108", "us": True, "public": False, "country": "US"},
    {"label": "Stanford", "qid": "Q41506", "us": True, "public": False, "country": "US"},
    {"label": "Harvard", "qid": "Q13371", "us": True, "public": False, "country": "US"},
    {"label": "University of Toronto", "qid": "Q180865", "us": False, "public": True, "country": "CA"},
    {"label": "University of Oxford", "qid": "Q34433", "us": False, "public": True, "country": "UK"},
    {"label": "University of Cambridge", "qid": "Q35794", "us": False, "public": True, "country": "UK"},
    {"label": "ETH Zurich", "qid": "Q185742", "us": False, "public": True, "country": "CH"},
    {"label": "Tsinghua University", "qid": "Q79875", "us": False, "public": True, "country": "CN"},
    {
        "label": "National University of Singapore",
        "qid": "Q738236",
        "us": False,
        "public": True,
        "country": "SG",
    },
]

C2024_ZIP = "https://nces.ed.gov/ipeds/datacenter/data/C2024_A.zip"


def wikidata_entities(qids: list[str]) -> dict[str, dict]:
    ids = "|".join(qids)
    r = requests.get(
        "https://www.wikidata.org/w/api.php",
        params={
            "action": "wbgetentities",
            "ids": ids,
            "format": "json",
            "props": "claims",
        },
        headers={"User-Agent": UA},
        timeout=120,
    )
    r.raise_for_status()
    return r.json().get("entities", {})


def latest_rank_for_edition(
    claims: dict, edition_qid: str
) -> tuple[int | None, str | None]:
    best_year = -1
    best_rank: int | None = None
    best_year_s: str | None = None
    for stmt in claims.get("P1352", []):
        qlist = stmt.get("qualifiers", {}).get("P459", [])
        edition_match = any(
            q.get("datavalue", {}).get("value", {}).get("id") == edition_qid for q in qlist
        )
        if not edition_match:
            continue
        amt = stmt.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("amount")
        if amt is None:
            continue
        rank = int(str(amt).lstrip("+"))
        year_int = 0
        year_s = "0000"
        for tq in stmt.get("qualifiers", {}).get("P585", []):
            tv = tq.get("datavalue", {}).get("value", {}).get("time", "")
            m = re.search(r"\+(\d{4})-", tv)
            if m:
                year_s = m.group(1)
                year_int = int(year_s)
        if year_int >= best_year:
            best_year = year_int
            best_rank = rank
            best_year_s = year_s if year_int > 0 else None
    return best_rank, best_year_s


def institution_row(p: dict[str, Any], ent: dict) -> dict[str, Any]:
    claims = ent.get("claims", {})
    qs_r, qs_y = latest_rank_for_edition(claims, QS)
    ar_r, ar_y = latest_rank_for_edition(claims, ARWU)
    return {
        "label": p["label"],
        "anchor": p["qid"] == "Q838330",
        "country": p.get("country", ""),
        "qs_rank": qs_r,
        "qs_year": qs_y,
        "arwu_rank": ar_r,
        "arwu_year": ar_y,
    }


def sort_institutions(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(r: dict[str, Any]) -> tuple:
        qr = r.get("qs_rank")
        return (qr is None, qr if qr is not None else 10**9, r["label"])

    return sorted(rows, key=key)


def rows_for_peer_subset(entities: dict[str, dict], pred) -> list[dict[str, Any]]:
    rows = []
    for p in PEERS:
        if not pred(p):
            continue
        ent = entities.get(p["qid"], {})
        rows.append(institution_row(p, ent))
    return sort_institutions(rows)


def download_c2024() -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    dest = RAW / "C2024_A.zip"
    if not dest.exists():
        print(f"Downloading {C2024_ZIP} …")
        r = requests.get(C2024_ZIP, headers={"User-Agent": UA}, timeout=300)
        r.raise_for_status()
        dest.write_bytes(r.content)
    return dest


def load_c2024_df(zip_path: Path) -> pd.DataFrame:
    inner = "c2024_a.csv"
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = [
            n
            for n in zf.namelist()
            if n.lower().endswith(".csv") and inner in n.lower() and "_rv" not in n.lower()
        ]
        if not names:
            raise FileNotFoundError(inner)
        names.sort()
        with zf.open(names[0]) as f:
            return pd.read_csv(f, dtype=str, low_memory=False)


def build_majors_from_ipeds() -> list[dict]:
    zip_path = download_c2024()
    df = load_c2024_df(zip_path)
    sub = df[df["UNITID"].astype(str).str.strip() == str(UNITID)].copy()
    if sub.empty:
        return []
    cip_col = "CIPCODE" if "CIPCODE" in sub.columns else "CIPCODE2020"
    tot = "CTOTALT"
    sub["_n"] = pd.to_numeric(sub[tot].astype(str).str.strip(), errors="coerce").fillna(0).astype(int)
    sub["_cip"] = sub[cip_col].astype(str).str.strip()
    g = sub.groupby("_cip", as_index=False)["_n"].sum()
    g = g[g["_cip"].str.len() > 0]
    g = g.sort_values("_n", ascending=False)
    rows = []
    for _, r in g.iterrows():
        rows.append(
            {
                "cipcode": r["_cip"],
                "program_label": f"CIP {r['_cip']}",
                "ipeds_awards": int(r["_n"]),
                "publisher_rank": None,
                "publisher": None,
                "source_url": None,
            }
        )
    return rows


def merge_optional_major_ranks(entries: list[dict]) -> None:
    if not OPTIONAL_MAJOR_RANKS.exists():
        return
    by_cip: dict[str, dict[str, Any]] = {}
    with OPTIONAL_MAJOR_RANKS.open(newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            cip = (row.get("cipcode") or row.get("CIPCODE") or "").strip()
            if not cip:
                continue
            pr = row.get("publisher_rank") or row.get("rank")
            try:
                rank_v = int(float(pr)) if pr not in (None, "") else None
            except ValueError:
                rank_v = None
            by_cip[cip] = {
                "publisher_rank": rank_v,
                "publisher": row.get("publisher") or row.get("source"),
                "source_url": row.get("source_url"),
                "program_label": row.get("program_label") or row.get("label"),
            }
    for e in entries:
        o = by_cip.get(e["cipcode"])
        if not o:
            continue
        if o.get("publisher_rank") is not None:
            e["publisher_rank"] = o["publisher_rank"]
        if o.get("publisher"):
            e["publisher"] = o["publisher"]
        if o.get("source_url"):
            e["source_url"] = o["source_url"]
        if o.get("program_label"):
            e["program_label"] = o["program_label"]


def sort_major_entries(entries: list[dict]) -> list[dict]:
    ranked = [e for e in entries if e.get("publisher_rank") is not None]
    unranked = [e for e in entries if e.get("publisher_rank") is None]
    ranked.sort(key=lambda e: (e["publisher_rank"], -e["ipeds_awards"]))
    unranked.sort(key=lambda e: -e["ipeds_awards"])
    return ranked + unranked


def main() -> None:
    qids = [p["qid"] for p in PEERS]
    entities = wikidata_entities(qids)

    global_rows = rows_for_peer_subset(entities, lambda _p: True)
    us_rows = rows_for_peer_subset(entities, lambda p: p["us"])
    public_rows = rows_for_peer_subset(entities, lambda p: p["public"])

    try:
        entries = build_majors_from_ipeds()
        merge_optional_major_ranks(entries)
        entries = sort_major_entries(entries)
    except Exception as e:  # noqa: BLE001
        print(f"warn: IPEDS majors: {e}", file=sys.stderr)
        entries = []

    snap = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    payload = {
        "meta": {
            "project": "BadgerNet 4.0",
            "tab": "rankings",
            "snapshot_date": snap,
            "degree_level": "all",
            "source": "wikidata_ipeds",
            "source_url": "https://www.wikidata.org/",
            "methodology": (
                "Single bundle for the Rankings tab. Institution tables use Wikidata `P1352` "
                "with `P459` = QS World University Rankings (Q1790510) and ARWU / Shanghai (Q478743), "
                "taking the latest qualifier year per edition. **Global** deliberately includes "
                "non-U.S. universities (Oxford, Cambridge, ETH Zurich, Tsinghua, NUS, Toronto, etc.) "
                "alongside U.S. peers so the comparison is not U.S.-only. **U.S.** and **Public** "
                "are filtered views of the same metrics on subsets of that peer list (see `country`, "
                "`us`, and `public` flags in harvest_rankings.py). Majors: IPEDS C2024_A completions "
                "by CIP for UNITID 240444; optional `data/raw/major_ranks.csv` merges publisher ranks."
            ),
            "disclaimer": (
                "Wikidata ranks are community-sourced and may disagree with official publisher tables. "
                "Verify before citing. IPEDS counts are administrative completions, not program quality ranks."
            ),
        },
        "sections": {
            "global": {
                "title": "World peer comparison",
                "blurb": (
                    "QS and ARWU positions for a curated mix of U.S. and non-U.S. research universities. "
                    "If a cell is empty, Wikidata had no rank statement for that edition."
                ),
                "institutions": global_rows,
            },
            "us": {
                "title": "U.S. institutions only",
                "blurb": (
                    "Same QS / ARWU metrics as the world tab, limited to peers flagged as United States "
                    "in the harvest script. This is **not** the same as a U.S.-national ranking list "
                    "(e.g. US News “national universities”)."
                ),
                "institutions": us_rows,
            },
            "public": {
                "title": "Public institutions only",
                "blurb": (
                    "Same metrics, limited to peers flagged as public (private U.S. schools like MIT, "
                    "Stanford, and Harvard are excluded here even though they appear in the world tab)."
                ),
                "institutions": public_rows,
            },
            "majors": {
                "title": "UW–Madison programs (IPEDS completions)",
                "blurb": (
                    "All CIP codes with total completions in IPEDS C2024_A for UW–Madison. "
                    "Optional publisher ranks merge from data/raw/major_ranks.csv."
                ),
                "entries": entries,
            },
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Remove legacy split files if present
    for legacy in (
        "rankings_global.json",
        "rankings_us.json",
        "rankings_public.json",
        "rankings_majors_uw.json",
    ):
        p = OUT.parent / legacy
        if p.exists():
            p.unlink()
            print(f"Removed legacy {legacy}")

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"  Global institutions: {len(global_rows)}, US: {len(us_rows)}, public: {len(public_rows)}")
    print(f"  Major rows: {len(entries)}")


if __name__ == "__main__":
    main()
