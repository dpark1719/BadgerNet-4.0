#!/usr/bin/env python3
"""
Build origins_undergrad.json from IPEDS Fall Enrollment EFC (residence of
first-time degree/certificate-seeking students — freshmen cohort).

Source: https://nces.ed.gov/ipeds/datacenter/ — file EF{year}C.zip
Institution: University of Wisconsin–Madison, UNITID 240444.

Pass --years 2019,2020,2021,2022 to emit per-fall-year `by_year` slices for the
UI year filter. Single year (default 2022) still works.

This is NOT “all enrolled undergraduates by home state”; it is the EFC
definition (first-time cohort). See meta.methodology in output.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Iterable

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


def build_us_states_rows(df: pd.DataFrame) -> list[dict]:
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
    return rows


def foreign_freshmen_count(df: pd.DataFrame) -> int:
    sub = df[(df["UNITID"].astype(str).str.strip() == str(UNITID)) & (df["EFCSTATE"].astype(str).str.strip() == "90")]
    if sub.empty:
        return 0
    v = pd.to_numeric(sub.iloc[0]["EFRES01"], errors="coerce")
    return int(v) if pd.notna(v) else 0


def parse_years(s: str) -> list[int]:
    parts = [p.strip() for p in s.replace(" ", "").split(",") if p.strip()]
    years = sorted({int(p) for p in parts})
    return years


def merge_us_by_year(years: Iterable[int]) -> list[dict]:
    acc: dict[str, dict[str, int]] = defaultdict(dict)
    for y in years:
        zip_path = download_zip(y)
        df = load_efc_csv(y, zip_path)
        ys = str(y)
        for row in build_us_states_rows(df):
            acc[row["label"]][ys] = row["value"]
    merged = []
    for label, by_y in acc.items():
        total = sum(by_y.values())
        merged.append({"label": label, "value": total, "by_year": dict(sorted(by_y.items()))})
    merged.sort(key=lambda x: -x["value"])
    return merged


def merge_foreign_by_year(years: Iterable[int]) -> dict:
    by_y: dict[str, int] = {}
    for y in years:
        zip_path = download_zip(y)
        df = load_efc_csv(y, zip_path)
        by_y[str(y)] = foreign_freshmen_count(df)
    return {"by_year": dict(sorted(by_y.items())), "total": sum(by_y.values())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--years",
        type=str,
        default="2022",
        help="Comma-separated IPEDS fall collection years, e.g. 2019,2020,2021,2022",
    )
    args = ap.parse_args()
    years = parse_years(args.years)
    y_min, y_max = min(years), max(years)

    if len(years) == 1:
        y = years[0]
        zip_path = download_zip(y)
        df = load_efc_csv(y, zip_path)
        us_data = [{"label": r["label"], "value": r["value"], "by_year": {str(y): r["value"]}} for r in build_us_states_rows(df)]
        foreign = foreign_freshmen_count(df)
        countries_data = [
            {
                "label": "Foreign countries (all, aggregated)",
                "value": foreign,
                "by_year": {str(y): foreign},
            },
        ]
        ay = f"{y - 1}-{str(y)[-2:]}"
        meth_us = (
            f"US states: IPEDS Fall Enrollment EF{y}C, residence of first-time "
            "degree/certificate-seeking undergraduate students (freshmen cohort), UNITID 240444. "
            "Foreign row (EFCSTATE 90): aggregated count only — IPEDS does not break out country here."
        )
    else:
        us_data = merge_us_by_year(years)
        fsum = merge_foreign_by_year(years)
        countries_data = [
            {
                "label": "Foreign countries (all, aggregated)",
                "value": fsum["total"],
                "by_year": fsum["by_year"],
            },
        ]
        ay = f"{y_min - 1}-{str(y_min)[-2:]} … {y_max - 1}-{str(y_max)[-2:]}"
        meth_us = (
            f"US states: IPEDS Fall Enrollment EF{y_min}C–EF{y_max}C (one slice per fall collection year), "
            "residence of first-time degree/certificate-seeking undergraduate students (freshmen cohort), "
            "UNITID 240444. Each `by_year` key is the EF collection year (e.g. 2022 = EF2022C). "
            "Foreign row (EFCSTATE 90): aggregated count only — IPEDS does not break out country here."
        )

    common = {
        "project": "BadgerNet 4.0",
        "snapshot_date": pd.Timestamp.utcnow().strftime("%Y-%m-%d"),
        "academic_year": ay,
    }

    payload = {
        "meta": {
            **common,
            "tab": "origins_undergraduate",
            "degree_level": "undergraduate",
            "source": "ipeds",
            "source_url": "https://nces.ed.gov/ipeds/datacenter/",
            "methodology": meth_us,
            "disclaimer": (
                "These are official IPEDS counts for the EF cohort definition above, not all UW undergraduates. "
                "Do not sum with other charts as a full enrollment census."
            ),
        },
        "charts": {
            "us_states": {
                "type": "bar",
                "title": (
                    f"US home state — first-time freshmen (IPEDS EF{y_min}C–EF{y_max}C, UW–Madison)"
                    if len(years) > 1
                    else f"US home state — first-time freshmen (IPEDS EF{years[0]}C, UW–Madison)"
                ),
                "data": us_data,
            },
            "countries": {
                "type": "bar",
                "title": (
                    f"International — foreign freshmen aggregate (IPEDS EF{y_min}–EF{y_max}, single bucket)"
                    if len(years) > 1
                    else f"International — aggregated foreign freshmen (IPEDS EF{years[0]}C, single bucket)"
                ),
                "data": countries_data,
            },
        },
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {OUT_JSON.relative_to(ROOT)} ({len(us_data)} state/territory rows, "
        f"years={years}, foreign_total={countries_data[0]['value']})",
    )


if __name__ == "__main__":
    main()
