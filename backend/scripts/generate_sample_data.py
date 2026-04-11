#!/usr/bin/env python3
"""Emit chart JSON bundles for the frontend (sample / dev data)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "frontend" / "public" / "data"

YEARS = list(range(2016, 2026))


def write(name: str, payload: object) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)}")


def trend_rows(
    base_1y: float,
    base_5y: float,
    base_10y: float,
    drift: tuple[float, float, float] = (0.15, 0.12, 0.1),
) -> list[dict[str, float | int]]:
    rows = []
    for i, year in enumerate(YEARS):
        rows.append(
            {
                "year": year,
                "w1y": round(base_1y + drift[0] * i, 2),
                "w5y": round(base_5y + drift[1] * i, 2),
                "w10y": round(base_10y + drift[2] * i, 2),
            }
        )
    return rows


def main() -> None:
    common = {
        "project": "BadgerNet 4.0",
        "snapshot_date": "2026-04-11",
        "academic_year": "2023-24",
    }

    trend_series = [
        {"dataKey": "w1y", "label": "1-year window", "color": "#c5050c"},
        {"dataKey": "w5y", "label": "5-year window", "color": "#1e3a8a"},
        {"dataKey": "w10y", "label": "10-year window", "color": "#047857"},
    ]

    write(
        "industry.json",
        {
            "meta": {
                **common,
                "tab": "industry",
                "degree_level": "all",
                "source": "sample",
                "source_url": None,
                "methodology": "Synthetic counts + trends for UI development. Replace with UW survey + LinkedIn rollups.",
                "disclaimer": "Not real UW–Madison statistics.",
            },
            "charts": {
                "by_industry": {
                    "type": "bar",
                    "title": "Alumni by industry (sample, latest snapshot)",
                    "data": [
                        {"label": "Technology", "value": 4200},
                        {"label": "Healthcare", "value": 3100},
                        {"label": "Finance", "value": 2400},
                        {"label": "Education", "value": 1900},
                        {"label": "Manufacturing", "value": 1200},
                        {"label": "Other", "value": 2800},
                    ],
                },
                "tech_share_trend": {
                    "type": "trend",
                    "title": "Technology sector share — synthetic trend (% of known industry)",
                    "x_key": "year",
                    "data": trend_rows(28.0, 26.2, 24.8),
                    "series": trend_series,
                },
            },
        },
    )

    write(
        "postgrad.json",
        {
            "meta": {
                **common,
                "tab": "postgrad",
                "degree_level": "all",
                "source": "sample",
                "methodology": "Synthetic continuation rate, degree-type mix, and trend.",
                "disclaimer": "Not from an official first-destination survey.",
            },
            "charts": {
                "continuation_rate": {
                    "type": "metric",
                    "title": "Continuing formal education within 1 year (sample)",
                    "value": 22.4,
                    "unit": "percent",
                },
                "continuation_trend": {
                    "type": "trend",
                    "title": "Continuing education rate — synthetic (% of cohort)",
                    "x_key": "year",
                    "data": trend_rows(19.5, 20.1, 21.0, drift=(0.25, 0.22, 0.18)),
                    "series": trend_series,
                },
                "by_degree_type": {
                    "type": "bar",
                    "title": "Next credential type (sample)",
                    "data": [
                        {"label": "Master’s", "value": 890},
                        {"label": "Doctorate", "value": 210},
                        {"label": "Professional (JD/MD/MBA)", "value": 140},
                        {"label": "Certificate / other", "value": 95},
                    ],
                },
            },
        },
    )

    write(
        "international.json",
        {
            "meta": {
                **common,
                "tab": "international_outcomes",
                "degree_level": "all",
                "source": "sample",
                "filter_fingerprint": "sample:no_filters",
                "methodology": (
                    "Population (target): non–U.S. citizens who came from abroad before UW. "
                    "Destination after UW: synthetic country mix; production = LinkedIn aggregate harvest "
                    "with documented filters (no API). Replace with real rollups only."
                ),
                "disclaimer": (
                    "Approximate and incomplete. LinkedIn-visible alumni are not a census; "
                    "citizenship and ‘from abroad’ are proxy-filtered, not administrative records."
                ),
            },
            "charts": {
                "destination_country": {
                    "type": "bar",
                    "title": "Post-UW country — sample (non-U.S. citizens from abroad)",
                    "data": [
                        {"label": "United States", "value": 450},
                        {"label": "India", "value": 180},
                        {"label": "China", "value": 120},
                        {"label": "South Korea", "value": 55},
                        {"label": "Canada", "value": 48},
                        {"label": "Other", "value": 210},
                    ],
                },
                "return_vs_stay_trend": {
                    "type": "trend",
                    "title": "Synthetic trend: share remaining in U.S. vs leaving (proxy metric)",
                    "x_key": "year",
                    "data": trend_rows(62.0, 58.0, 55.0, drift=(0.4, 0.35, 0.3)),
                    "series": trend_series,
                },
            },
        },
    )

    def origins_bundle(degree: str, tab: str, title_suffix: str) -> dict:
        scale = {"undergraduate": 1.0, "graduate": 0.42, "doctorate": 0.11}[degree]
        return {
            "meta": {
                **common,
                "tab": tab,
                "degree_level": degree,
                "source": "sample",
                "methodology": (
                    f"Synthetic US state + country origin for {degree} enrollment. "
                    "Production: IPEDS Fall Enrollment / CDS by level (UnitID 240444 = UW–Madison)."
                ),
                "disclaimer": "Not official IPEDS figures; for UI development only.",
            },
            "charts": {
                "us_states": {
                    "type": "bar",
                    "title": f"US home state — enrolled (sample, {title_suffix})",
                    "data": [
                        {"label": "Wisconsin", "value": int(8200 * scale)},
                        {"label": "Illinois", "value": int(2100 * scale)},
                        {"label": "Minnesota", "value": int(980 * scale)},
                        {"label": "California", "value": int(720 * scale)},
                        {"label": "Other", "value": int(5400 * scale)},
                    ],
                },
                "countries": {
                    "type": "bar",
                    "title": f"Country of origin — international enrolled (sample, {title_suffix})",
                    "data": [
                        {"label": "China", "value": int(1200 * scale)},
                        {"label": "India", "value": int(890 * scale)},
                        {"label": "South Korea", "value": int(410 * scale)},
                        {"label": "Canada", "value": int(260 * scale)},
                        {"label": "Other", "value": int(1500 * scale)},
                    ],
                },
                "enrollment_intl_trend": {
                    "type": "trend",
                    "title": f"International enrollment index — synthetic ({title_suffix})",
                    "x_key": "year",
                    "data": trend_rows(
                        100 * scale,
                        98 * scale,
                        95 * scale,
                        drift=(0.8 * scale, 0.7 * scale, 0.6 * scale),
                    ),
                    "series": trend_series,
                },
            },
        }

    write("origins_undergrad.json", origins_bundle("undergraduate", "origins_undergraduate", "UG"))
    write("origins_graduate.json", origins_bundle("graduate", "origins_graduate", "Grad"))
    write("origins_doctorate.json", origins_bundle("doctorate", "origins_doctorate", "PhD / doctorate"))

    write(
        "meta.json",
        {
            "site": {
                "name": "BadgerNet 4.0",
                "tagline": "Where UW–Madison students and alumni go — data-driven views (in progress).",
            },
            "github_repo": "https://github.com/dpark1719/BadgerNet-4.0",
            "github_project": "https://github.com/users/dpark1719/projects/2",
            "methodology_blurb": (
                "This app loads static JSON from /data. Six top-level tabs: Industry, Post-grad education, "
                "International outcomes, and three Student origins levels (UG, grad, doctorate). "
                "Trend charts use 1y / 5y / 10y-style series (synthetic until real pipelines land). "
                "International outcomes target non–U.S. citizens from abroad; LinkedIn harvest is aggregate-only, no API."
            ),
            "tabs": [
                {"id": "industry", "label": "Industry"},
                {"id": "postgrad", "label": "Post-grad education"},
                {"id": "international", "label": "International outcomes"},
                {"id": "origins_undergrad", "label": "Origins — Undergraduate"},
                {"id": "origins_graduate", "label": "Origins — Graduate"},
                {"id": "origins_doctorate", "label": "Origins — Doctorate"},
            ],
        },
    )


if __name__ == "__main__":
    main()
