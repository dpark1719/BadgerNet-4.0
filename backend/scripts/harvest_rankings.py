#!/usr/bin/env python3
"""
Build a single rankings bundle: frontend/public/data/rankings.json

- Institution tables: Wikidata P1352 + P459 for QS World (Q1790510) and ARWU (Q478743).
  **Global** peer set deliberately mixes U.S. and non-U.S. universities so the world view
  is not U.S.-only (earlier versions were mostly U.S. by design of the peer list).
- Sub-sections inside the app: global | us | public | majors (no separate top-level tabs).
- UW majors: IPEDS Completions C2024_A (UNITID 240444); NCES CIP-2020 titles; optional
  data/raw/major_ranks.csv; optional labels from frontend/public/data/majors/index.json.

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
CIP_CACHE = ROOT / "data" / "raw" / "cip" / "CIPCode2020.csv"
CIP_LOOKUP_URL = "https://nces.ed.gov/ipeds/cipcode/Files/CIPCode2020.csv"
MAJORS_INDEX_JSON = ROOT / "frontend" / "public" / "data" / "majors" / "index.json"
OPTIONAL_MAJOR_RANKS = ROOT / "data" / "raw" / "major_ranks.csv"
# UW Programs tab: only include rows with publisher vs-peer rank in [1, TOP_PUBLISHER_RANK].
TOP_PUBLISHER_RANK = 10

UNITID = 240444
UA = "BadgerNet/4.0 (https://github.com/dpark1719/BadgerNet-4.0; harvest_rankings)"

QS = "Q1790510"
ARWU = "Q478743"
US_Q = "Q30"
WDQS = "https://query.wikidata.org/sparql"
# Pre-fetch ranks within this many integers of UW for neighborhood + UI expand (no re-query).
RANK_SURROUND_HALF_WIDTH = 55

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
            "props": "labels|claims",
        },
        headers={"User-Agent": UA},
        timeout=120,
    )
    r.raise_for_status()
    return r.json().get("entities", {})


def wikidata_entities_batched(qids: list[str], batch_size: int = 45) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i in range(0, len(qids), batch_size):
        out.update(wikidata_entities(qids[i : i + batch_size]))
    return out


def year_from_wd_time(timev: str) -> str | None:
    """Calendar year from WD time value (SPARQL or wb JSON), e.g. +2025-01-01T00:00:00Z."""
    if not timev:
        return None
    m = re.search(r"(\d{4})-\d{2}-\d{2}", timev)
    if m:
        return m.group(1)
    m = re.search(r"(\d{4})", timev)
    return m.group(1) if m else None


def dedupe_band_by_qid_prefer_year(
    raw: list[dict[str, Any]], uw_year: str | None
) -> list[dict[str, Any]]:
    """One row per item; prefer the WD statement year matching uw_year, else closest calendar year."""
    by: dict[str, list[dict[str, Any]]] = {}
    for x in raw:
        by.setdefault(x["qid"], []).append(x)
    uy = int(uw_year) if uw_year and str(uw_year).isdigit() else None
    out: list[dict[str, Any]] = []
    for _qid, variants in by.items():
        if uy is not None:
            match = [v for v in variants if v.get("year") == uw_year]
            if match:
                out.append(match[0])
                continue
            scored: list[tuple[int, int, dict[str, Any]]] = []
            for v in variants:
                y = v.get("year")
                if y and str(y).isdigit():
                    yi = int(str(y))
                    scored.append((abs(yi - uy), -yi, v))
            if scored:
                scored.sort()
                out.append(scored[0][2])
                continue
        best_y = -1
        best_v = variants[0]
        for v in variants:
            y = v.get("year")
            yi = int(y) if y and str(y).isdigit() else -1
            if yi > best_y:
                best_y = yi
                best_v = v
        out.append(best_v)
    return out


def sparql_rank_band_for_edition(
    edition_qid: str,
    rank_low: int,
    rank_high: int,
) -> list[dict[str, Any]]:
    """Raw rows: qid, rank (int), year (str|None), p17 (Q-id|None)."""
    q = f"""
SELECT DISTINCT ?item ?rank ?time ?country WHERE {{
  ?item p:P1352 ?st .
  ?st ps:P1352 ?rank .
  ?st pq:P459 wd:{edition_qid} .
  ?st pq:P585 ?time .
  OPTIONAL {{ ?item wdt:P17 ?country . }}
  BIND(xsd:integer(xsd:decimal(?rank)) AS ?ri)
  FILTER(?ri >= {int(rank_low)} && ?ri <= {int(rank_high)})
}}
LIMIT 3000
"""
    r = requests.get(
        WDQS,
        params={"query": q, "format": "json"},
        headers={"User-Agent": UA, "Accept": "application/sparql-results+json"},
        timeout=180,
    )
    r.raise_for_status()
    data = r.json()
    out: list[dict[str, Any]] = []
    for b in data.get("results", {}).get("bindings", []):
        item_uri = b.get("item", {}).get("value", "")
        m = re.search(r"/(Q\d+)$", item_uri)
        if not m:
            continue
        qid = m.group(1)
        raw_rank = b.get("rank", {}).get("value", "")
        try:
            ri = int(float(raw_rank))
        except ValueError:
            continue
        timev = b.get("time", {}).get("value", "")
        y = year_from_wd_time(timev)
        c_uri = b.get("country", {}).get("value", "")
        cm = re.search(r"/(Q\d+)$", c_uri) if c_uri else None
        cq = cm.group(1) if cm else None
        out.append({"qid": qid, "rank": ri, "year": y, "p17": cq})
    return out


def build_rank_surround_slice(
    edition_qid: str,
    metric_key: str,
    uw_rank: int | None,
    uw_year: str | None,
) -> dict[str, Any] | None:
    if uw_rank is None:
        return None
    lo = max(1, uw_rank - RANK_SURROUND_HALF_WIDTH)
    hi = uw_rank + RANK_SURROUND_HALF_WIDTH
    try:
        raw = sparql_rank_band_for_edition(edition_qid, lo, hi)
    except Exception as e:  # noqa: BLE001
        print(f"warn: WDQS {metric_key} band: {e}", file=sys.stderr)
        return None
    raw = dedupe_band_by_qid_prefer_year(raw, uw_year)
    if uw_year:
        strict = [x for x in raw if x.get("year") == uw_year]
        if strict:
            raw = strict
        else:
            print(
                f"warn: WDQS {metric_key}: no rows with statement year {uw_year}; keeping merged years",
                file=sys.stderr,
            )
    by_qid: dict[str, dict[str, Any]] = {x["qid"]: x for x in raw}
    p17s: set[str] = {x["p17"] for x in by_qid.values() if x.get("p17")}
    country_q_labels = prefetch_country_labels(p17s)
    qids = list(by_qid.keys())
    if not qids:
        return None
    entities = wikidata_entities_batched(qids)
    rows: list[dict[str, Any]] = []
    for qid, st in by_qid.items():
        ent = entities.get(qid, {})
        label = ent.get("labels", {}).get("en", {}).get("value") or qid
        p17 = st.get("p17")
        ctag = country_q_labels.get(p17, "") if p17 else ""
        is_us = p17 == US_Q if p17 else False
        rk = st["rank"]
        yr = st.get("year")
        claims = ent.get("claims", {})
        qs_r, qs_y = (rk, yr) if metric_key == "qs" else latest_rank_for_edition(claims, QS)
        ar_r, ar_y = (rk, yr) if metric_key == "arwu" else latest_rank_for_edition(claims, ARWU)
        rows.append(
            {
                "qid": qid,
                "label": label,
                "anchor": qid == "Q838330",
                "country": ctag,
                "is_us": is_us,
                "qs_rank": qs_r,
                "qs_year": qs_y,
                "arwu_rank": ar_r,
                "arwu_year": ar_y,
            }
        )
    if metric_key == "qs":
        rows.sort(key=lambda r: (r["qs_rank"] is None, r["qs_rank"] or 10**9, r["label"]))
    else:
        rows.sort(key=lambda r: (r["arwu_rank"] is None, r["arwu_rank"] or 10**9, r["label"]))
    return {
        "edition_qid": edition_qid,
        "year": uw_year,
        "center_rank": uw_rank,
        "band_half_width": RANK_SURROUND_HALF_WIDTH,
        "institutions": rows,
    }


def prefetch_country_labels(p17_qids: set[str]) -> dict[str, str]:
    if not p17_qids:
        return {}
    ents = wikidata_entities_batched(list(p17_qids))
    out: dict[str, str] = {}
    for q, ent in ents.items():
        lab = ent.get("labels", {}).get("en", {}).get("value")
        if lab:
            out[q] = lab
    return out


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


def norm_cip_code_cell(cell: str) -> str:
    """NCES CSV sometimes stores codes like =\\"11.0701\\"."""
    s = (cell or "").strip().strip('"')
    if s.startswith("="):
        s = s[1:]
    return s.strip().strip('"').strip()


def load_majors_index_cip_labels() -> dict[str, str]:
    """CIP -> display label from bundled majors index (overrides NCES title when present)."""
    if not MAJORS_INDEX_JSON.exists():
        return {}
    try:
        data = json.loads(MAJORS_INDEX_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    out: dict[str, str] = {}
    for m in data.get("majors", []):
        cip = str(m.get("cip") or "").strip()
        lab = str(m.get("label") or "").strip()
        if cip and lab:
            out[cip] = lab
    return out


def download_cip_lookup_table() -> Path:
    CIP_CACHE.parent.mkdir(parents=True, exist_ok=True)
    if not CIP_CACHE.exists():
        print(f"Downloading {CIP_LOOKUP_URL} …")
        r = requests.get(CIP_LOOKUP_URL, headers={"User-Agent": UA}, timeout=300)
        r.raise_for_status()
        CIP_CACHE.write_bytes(r.content)
    return CIP_CACHE


def load_cip_2020_titles(path: Path) -> dict[str, str]:
    """Map 6-digit CIP '##.####' -> NCES CIPTitle (trailing period removed)."""
    out: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            code = norm_cip_code_cell(row.get("CIPCode") or "")
            if not re.fullmatch(r"\d{2}\.\d{4}", code):
                continue
            title = (row.get("CIPTitle") or "").strip().strip('"')
            if title.endswith("."):
                title = title[:-1].strip()
            if title:
                out[code] = title
    return out


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
    cip_titles = load_cip_2020_titles(download_cip_lookup_table())
    index_labels = load_majors_index_cip_labels()
    rows = []
    for _, r in g.iterrows():
        cip = str(r["_cip"]).strip()
        if cip in index_labels:
            label = index_labels[cip]
        elif cip in cip_titles:
            label = cip_titles[cip]
        elif re.fullmatch(r"\d{2}\.\d{4}", cip):
            label = f"CIP {cip}"
        else:
            label = f"Unclassified reporting ({cip})"
        rows.append(
            {
                "cipcode": cip,
                "program_label": label,
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


def filter_majors_publisher_top(entries: list[dict], max_rank: int = TOP_PUBLISHER_RANK) -> list[dict]:
    """Programs with a publisher vs-peer rank from 1 to max_rank (inclusive); sorted by rank then name."""
    out: list[dict] = []
    for e in entries:
        pr = e.get("publisher_rank")
        if pr is None:
            continue
        try:
            r = int(pr)
        except (TypeError, ValueError):
            continue
        if 1 <= r <= max_rank:
            out.append(e)
    out.sort(key=lambda x: (x["publisher_rank"], str(x.get("program_label") or "").lower()))
    return out


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
        entries = filter_majors_publisher_top(entries)
    except Exception as e:  # noqa: BLE001
        print(f"warn: IPEDS majors: {e}", file=sys.stderr)
        entries = []

    uw_ent = entities.get("Q838330", {})
    uw_claims = uw_ent.get("claims", {})
    uw_qs_r, uw_qs_y = latest_rank_for_edition(uw_claims, QS)
    uw_ar_r, uw_ar_y = latest_rank_for_edition(uw_claims, ARWU)

    rank_surround: dict[str, Any] = {}
    qs_slice = build_rank_surround_slice(QS, "qs", uw_qs_r, uw_qs_y)
    if qs_slice:
        rank_surround["qs"] = qs_slice
    ar_slice = build_rank_surround_slice(ARWU, "arwu", uw_ar_r, uw_ar_y)
    if ar_slice:
        rank_surround["arwu"] = ar_slice

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
                "taking the latest qualifier year per edition. `rank_surround` adds WDQS slices of "
                "institutions whose published rank is within ±55 of UW for the same statement year. "
                "**Global** deliberately includes "
                "non-U.S. universities (Oxford, Cambridge, ETH Zurich, Tsinghua, NUS, Toronto, etc.) "
                "alongside U.S. peers so the comparison is not U.S.-only. **U.S.** and **Public** "
                "are filtered views of the same metrics on subsets of that peer list (see `country`, "
                "`us`, and `public` flags in harvest_rankings.py). Majors: optional "
                "`data/raw/major_ranks.csv` supplies publisher vs-peer ranks; bundle keeps only ranks "
                f"1–{TOP_PUBLISHER_RANK} with NCES CIP titles from IPEDS C2024_A completions context."
            ),
            "disclaimer": (
                "Wikidata ranks are community-sourced and may disagree with official publisher tables. "
                "Verify before citing. IPEDS counts are administrative completions, not program quality ranks."
            ),
        },
        "rank_surround": rank_surround,
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
                "title": "UW–Madison programs — top publisher ranks (1–10)",
                "blurb": (
                    "Only programs with an external publisher rank vs other schools (ranks 1–"
                    f"{TOP_PUBLISHER_RANK}). Multiple UW programs that share the same national rank "
                    "are listed together under that rank. Merge ranks from `data/raw/major_ranks.csv` "
                    "and re-run harvest. CIP labels use NCES CIP-2020 titles."
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
    if rank_surround.get("qs"):
        print(f"  QS rank_surround rows: {len(rank_surround['qs']['institutions'])}")
    if rank_surround.get("arwu"):
        print(f"  ARWU rank_surround rows: {len(rank_surround['arwu']['institutions'])}")


if __name__ == "__main__":
    main()
