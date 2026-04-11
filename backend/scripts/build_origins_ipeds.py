#!/usr/bin/env python3
"""
Build origins_undergrad.json from IPEDS Fall Enrollment EF2022C (residence of
first-time degree/certificate-seeking students — freshmen cohort).

Source: https://nces.ed.gov/ipeds/datacenter/ — file EF{year}C.zip
Institution: University of Wisconsin–Madison, UNITID 240444.

This is NOT “all enrolled undergraduates by home state”; it is the EF2022C
definition (first-time cohort). See meta.methodology in output.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "ipeds"
OUT_JSON = ROOT / "frontend" / "public" / "data" / "origins_undergrad.json"

UNITID = 240444
ZIP_TMPL = "https://nces.ed.gov/ipeds/datacenter/data/EF{year}C.zip"
CSV_TMPL = "ef{year}c.csv"

sys.path.insert(0, str(ROOT / "backend"))
from lib.us_fips import FIPS_TO_LABEL, SKIP_EFCSTATE  # noqa: E402


def download_zip(year: int) -> Path:
    RAW.mkdir(parents=True, exist_ok=True)
    url = ZIP_TMPL.format(year=year)
    dest = RAW / f"EF{year}C.zip"
    if not dest.exists():
        print(f"Downloading {url} …")
        r = requests.get(url, timeout=300)
        r.raise_for_status()
        dest.write_bytes(r.content)
    return dest


def load_efc_csv(year: int, zip_path: Path) -> pd.DataFrame:
    inner = CSV_TMPL.format(year=year).lower()
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = [
            n
            for n in zf.namelist()
            if n.lower().endswith(".csv") and inner in n.lower() and "_rv" not in n.lower()
        ]
        if not names:
            raise FileNotFoundError(f"No {inner} csv in {zip_path}")
        names.sort()
        with zf.open(names[0]) as f:
            return pd.read_csv(f, dtype=str, low_memory=False)


def build_us_states(df: pd.DataFrame) -> list[dict]:
    sub = df[df["UNITID"].astype(str).str.strip() == str(UNITID)].copy()
    sub["efc"] = sub["EFCSTATE"].astype(str).str.strip()
    sub["n"] = pd.to_numeric(sub["EFRES01"].astype(str).str.strip(), errors="coerce").fillna(0).astype(int)
    rows = []
    for _, r in sub.iterrows():
        code = r["efc"]
        if code in SKIP_EFCSTATE:
            continue
        label = FIPS_TO_LABEL.get(code, f"State/region FIPS {code}")
        rows.append({"label": label, "value": int(r["n"]), "fips": code})
    rows.sort(key=lambda x: -x["value"])
    return [{"label": x["label"], "value": x["value"]} for x in rows]


def foreign_freshmen_count(df: pd.DataFrame) -> int:
    sub = df[(df["UNITID"].astype(str).str.strip() == str(UNITID)) & (df["EFCSTATE"].astype(str).str.strip() == "90")]
    if sub.empty:
        return 0
    v = pd.to_numeric(sub.iloc[0]["EFRES01"], errors="coerce")
    return int(v) if pd.notna(v) else 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2022, help="IPEDS fall collection year (e.g. 2022 for EF2022C)")
    args = ap.parse_args()

    zip_path = download_zip(args.year)
    df = load_efc_csv(args.year, zip_path)
    us_states = build_us_states(df)
    foreign = foreign_freshmen_count(df)

    common = {
        "project": "BadgerNet 4.0",
        "snapshot_date": pd.Timestamp.utcnow().strftime("%Y-%m-%d"),
        "academic_year": f"{args.year - 1}-{str(args.year)[-2:]}",
    }

    payload = {
        "meta": {
            **common,
            "tab": "origins_undergraduate",
            "degree_level": "undergraduate",
            "source": "ipeds",
            "source_url": "https://nces.ed.gov/ipeds/datacenter/",
            "methodology": (
                f"US states: IPEDS Fall Enrollment EF{args.year}C, residence of first-time "
                "degree/certificate-seeking undergraduate students (freshmen cohort), UNITID 240444. "
                "Foreign row (EFCSTATE 90): aggregated count only — IPEDS does not break out country here."
            ),
            "disclaimer": (
                "These are official IPEDS counts for the EF cohort definition above, not all UW undergraduates. "
                "Do not sum with other charts as a full enrollment census."
            ),
        },
        "charts": {
            "us_states": {
                "type": "bar",
                "title": f"US home state — first-time freshmen (IPEDS EF{args.year}C, UW–Madison)",
                "data": us_states,
            },
            "countries": {
                "type": "bar",
                "title": "International — aggregated foreign freshmen (IPEDS EF2022C, single bucket)",
                "data": [
                    {"label": "Foreign countries (all, aggregated)", "value": foreign},
                ],
            },
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSON.relative_to(ROOT)} ({len(us_states)} state/territory rows, foreign={foreign})")


if __name__ == "__main__":
    main()
