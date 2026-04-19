#!/usr/bin/env python3
"""Emit chart JSON bundles for the frontend (sample / dev data)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from backend.lib.cohort_year_split import (  # noqa: E402
    YEARS,
    bars_with_years,
    pct_by_year,
    sankey_links_with_years,
)
from backend.lib.majors_index import sync_majors_index  # noqa: E402
OUT = ROOT / "frontend" / "public" / "data"


def write(name: str, payload: object) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
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
        "academic_year": "2016–25 cohorts (pooled; filter years in UI)",
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
                "methodology": (
                    "Synthetic counts + trends for UI development. Replace with UW survey + LinkedIn rollups. "
                    "The “public spotlight” chart is a **hand-curated demo** of how you might surface employers "
                    "named in UW news or annual reports — not inferred from private profiles."
                ),
                "disclaimer": "Not real UW–Madison statistics.",
            },
            "charts": {
                "by_industry": {
                    "type": "bar",
                    "title": "Alumni by industry (sample, pooled cohort years)",
                    "data": bars_with_years(
                        [
                            {"label": "Technology", "value": 4200},
                            {"label": "Healthcare", "value": 3100},
                            {"label": "Finance", "value": 2400},
                            {"label": "Education", "value": 1900},
                            {"label": "Manufacturing", "value": 1200},
                            {"label": "Other", "value": 2800},
                        ],
                        11_001,
                    ),
                },
                "tech_share_trend": {
                    "type": "trend",
                    "title": "Technology sector share — synthetic trend (% of known industry)",
                    "x_key": "year",
                    "data": trend_rows(28.0, 26.2, 24.8),
                    "series": trend_series,
                },
                "top_employers": {
                    "type": "bar",
                    "title": "Top employers (sample, all majors, pooled years)",
                    "data": bars_with_years(
                        [
                            {"label": "Google", "value": 890},
                            {"label": "Epic", "value": 720},
                            {"label": "Microsoft", "value": 610},
                            {"label": "Amazon", "value": 540},
                            {"label": "UW–Madison", "value": 480},
                            {"label": "Deloitte", "value": 390},
                            {"label": "JPMorgan Chase", "value": 340},
                            {"label": "Other / unknown", "value": 12000},
                        ],
                        12_500,
                    ),
                },
                "employer_public_spotlight": {
                    "type": "bar",
                    "title": "Employers in public UW storytelling (curated sample, not placement data)",
                    "data": bars_with_years(
                        [
                            {"label": "Epic Systems", "value": 38},
                            {"label": "Google", "value": 31},
                            {"label": "American Family Insurance", "value": 24},
                            {"label": "JPMorgan Chase", "value": 19},
                            {"label": "GE Healthcare", "value": 16},
                            {"label": "Other mentions", "value": 52},
                        ],
                        12_900,
                    ),
                },
                "career_flow": {
                    "type": "sankey",
                    "title": "Illustrative career stages — all majors (first job → later career)",
                    "nodes": [
                        {"id": "e_intern", "label": "Internship"},
                        {"id": "e_entry", "label": "First job after graduation"},
                        {"id": "m_ic", "label": "Mid-career: specialist (not managing people)"},
                        {"id": "m_mgmt", "label": "Mid-career: people manager"},
                        {"id": "s_lead", "label": "Later career: lead or principal expert"},
                        {"id": "s_exec", "label": "Later career: executive or founder"},
                    ],
                    "links": sankey_links_with_years(
                        [
                            {"source": "e_intern", "target": "e_entry", "value": 2400},
                            {"source": "e_intern", "target": "m_ic", "value": 800},
                            {"source": "e_entry", "target": "m_ic", "value": 3200},
                            {"source": "e_entry", "target": "m_mgmt", "value": 900},
                            {"source": "m_ic", "target": "s_lead", "value": 1400},
                            {"source": "m_ic", "target": "s_exec", "value": 220},
                            {"source": "m_mgmt", "target": "s_exec", "value": 410},
                            {"source": "m_mgmt", "target": "s_lead", "value": 380},
                        ],
                        13_700,
                    ),
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
                "methodology": (
                    "Synthetic continuation rate, credential-type mix, trend, and **illustrative** grad/PhD "
                    "destination counts (not a real UW tabulation). Replace with First Destination Survey "
                    "or other UW-published tables."
                ),
                "disclaimer": (
                    "Not from an official first-destination survey. Institution list is demo-only until you "
                    "import real FDS / outcomes data."
                ),
            },
            "charts": {
                "continuation_rate": {
                    "type": "metric",
                    "title": "Continuing formal education within 1 year (sample)",
                    "value": 22.4,
                    "unit": "percent",
                    "by_year": pct_by_year(22.4, 88_001),
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
                    "title": "Next credential type (sample, pooled years)",
                    "data": bars_with_years(
                        [
                            {"label": "Master’s", "value": 890},
                            {"label": "Doctorate", "value": 210},
                            {"label": "Professional (JD/MD/MBA)", "value": 140},
                            {"label": "Certificate / other", "value": 95},
                        ],
                        14_100,
                    ),
                },
                "grad_phd_destinations": {
                    "type": "bar",
                    "title": "Further study — sample grad / PhD destinations (illustrative counts)",
                    "data": bars_with_years(
                        [
                            {"label": "UW–Madison (continuing)", "value": 612},
                            {"label": "University of Michigan", "value": 198},
                            {"label": "Northwestern University", "value": 156},
                            {"label": "University of Chicago", "value": 134},
                            {"label": "MIT", "value": 112},
                            {"label": "Stanford University", "value": 98},
                            {"label": "Harvard University", "value": 92},
                            {"label": "UC Berkeley", "value": 88},
                            {"label": "Cornell University", "value": 76},
                            {"label": "Georgia Institute of Technology", "value": 71},
                            {"label": "Johns Hopkins University", "value": 64},
                            {"label": "Duke University", "value": 58},
                            {"label": "UCLA", "value": 54},
                            {"label": "University of Minnesota", "value": 49},
                            {"label": "University of Illinois Urbana-Champaign", "value": 45},
                            {"label": "University of Wisconsin Medical School (MD)", "value": 41},
                            {"label": "Other / not specified", "value": 520},
                        ],
                        15_200,
                    ),
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
                    "with documented filters (no API). Replace with real rollups only. "
                    "Open Doors bars: rounded U.S.-level totals from IIE Open Doors "
                    "(https://opendoorsdata.org/) for national scale only — not UW-specific."
                ),
                "disclaimer": (
                    "Approximate and incomplete. LinkedIn-visible alumni are not a census; "
                    "citizenship and ‘from abroad’ are proxy-filtered, not administrative records. "
                    "Open Doors figures are national aggregates."
                ),
            },
            "charts": {
                "post_graduation_destination_country": {
                    "type": "bar",
                    "title": "Where alumni went after UW — by country (sample)",
                    "data": bars_with_years(
                        [
                            {"label": "United States", "value": 450},
                            {"label": "India", "value": 180},
                            {"label": "China", "value": 120},
                            {"label": "South Korea", "value": 55},
                            {"label": "Canada", "value": 48},
                            {"label": "Other", "value": 210},
                        ],
                        16_300,
                    ),
                },
                "return_vs_stay_trend": {
                    "type": "trend",
                    "title": "Synthetic trend: share remaining in U.S. vs leaving (proxy metric)",
                    "x_key": "year",
                    "data": trend_rows(62.0, 58.0, 55.0, drift=(0.4, 0.35, 0.3)),
                    "series": trend_series,
                },
                "open_doors_national_context": {
                    "type": "bar",
                    "title": "National mobility context (IIE Open Doors — U.S. totals, not UW)",
                    "data": [
                        {
                            "label": "International students in the U.S. (≈2023/24 headline total)",
                            "value": 1106104,
                        },
                        {
                            "label": "U.S. students studying abroad for credit (≈2022/23 headline total)",
                            "value": 280782,
                        },
                    ],
                },
            },
        },
    )

    def origins_bundle(degree: str, tab: str, title_suffix: str) -> dict:
        scale = {"undergraduate": 1.0, "graduate": 0.42, "doctorate": 0.11}[degree]
        oseed = {
            "origins_undergraduate": 201_001,
            "origins_graduate": 202_002,
            "origins_doctorate": 203_003,
        }[tab]
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
                    "data": bars_with_years(
                        [
                            {"label": "Wisconsin", "value": int(8200 * scale)},
                            {"label": "Illinois", "value": int(2100 * scale)},
                            {"label": "Minnesota", "value": int(980 * scale)},
                            {"label": "California", "value": int(720 * scale)},
                            {"label": "Other", "value": int(5400 * scale)},
                        ],
                        oseed,
                    ),
                },
                "countries": {
                    "type": "bar",
                    "title": f"Country of origin — international enrolled (sample, {title_suffix})",
                    "data": bars_with_years(
                        [
                            {"label": "China", "value": int(1200 * scale)},
                            {"label": "India", "value": int(890 * scale)},
                            {"label": "South Korea", "value": int(410 * scale)},
                            {"label": "Canada", "value": int(260 * scale)},
                            {"label": "Other", "value": int(1500 * scale)},
                        ],
                        oseed + 800,
                    ),
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

    def major_industry_bundle(
        major_id: str,
        label: str,
        employers: list,
        sankey: dict,
        *,
        cip: str | None = None,
        year_seed: int = 400_000,
    ) -> dict:
        meta = {
            **common,
            "tab": "industry",
            "major_id": major_id,
            "degree_level": "undergraduate",
            "source": "sample",
            "major_display_name": label,
            "methodology": (
                f"Synthetic industry, employer, and career-flow aggregates for major “{label}”. "
                "Production: LinkedIn harvest rollups by field-of-study filter + aggregation script."
            ),
            "disclaimer": "Not real UW–Madison statistics; major slice for UI development only.",
        }
        if cip:
            meta["major_cip"] = cip
        return {
            "meta": meta,
            "charts": {
                "by_industry": {
                    "type": "bar",
                    "title": f"Alumni by industry — {label} (sample, pooled years)",
                    "data": bars_with_years(sankey["by_industry_bars"], year_seed),
                },
                "top_employers": {
                    "type": "bar",
                    "title": f"Top employers — {label} (sample, pooled years)",
                    "data": bars_with_years(employers, year_seed + 5000),
                },
                "career_flow": {
                    "type": "sankey",
                    "title": f"Illustrative job stages — {label} (sample, not real counts)",
                    "nodes": sankey["nodes"],
                    "links": sankey_links_with_years(sankey["links"], year_seed + 2000),
                },
                "tech_share_trend": {
                    "type": "trend",
                    "title": f"Tech-sector share trend — {label} (sample)",
                    "x_key": "year",
                    "data": trend_rows(52.0, 48.0, 45.0, drift=(0.2, 0.18, 0.15)),
                    "series": trend_series,
                },
            },
        }

    cs_sankey = {
        "by_industry_bars": [
            {"label": "Software / internet", "value": 3100},
            {"label": "Finance / fintech", "value": 420},
            {"label": "Healthcare IT", "value": 380},
            {"label": "Defense / aerospace", "value": 290},
            {"label": "Other", "value": 910},
        ],
        "nodes": [
            {"id": "cs_intern", "label": "Internship (writing software)"},
            {"id": "cs_junior", "label": "Junior software engineer"},
            {"id": "cs_swe", "label": "Software engineer"},
            {"id": "cs_staff", "label": "Staff or principal engineer"},
            {"id": "cs_pm", "label": "Product manager"},
            {"id": "cs_exec", "label": "Director, VP, or startup founder"},
        ],
        "links": [
            {"source": "cs_intern", "target": "cs_junior", "value": 980},
            {"source": "cs_intern", "target": "cs_swe", "value": 320},
            {"source": "cs_junior", "target": "cs_swe", "value": 1500},
            {"source": "cs_junior", "target": "cs_pm", "value": 280},
            {"source": "cs_swe", "target": "cs_staff", "value": 620},
            {"source": "cs_swe", "target": "cs_exec", "value": 90},
            {"source": "cs_pm", "target": "cs_exec", "value": 110},
            {"source": "cs_staff", "target": "cs_exec", "value": 140},
        ],
    }
    cs_employers = [
        {"label": "Google", "value": 410},
        {"label": "Microsoft", "value": 290},
        {"label": "Amazon", "value": 260},
        {"label": "Meta", "value": 180},
        {"label": "Epic", "value": 170},
        {"label": "Apple", "value": 120},
        {"label": "Other", "value": 2850},
    ]
    write(
        "majors/computer_science.json",
        major_industry_bundle(
            "computer_science",
            "Computer Sciences, B.S.",
            cs_employers,
            cs_sankey,
            cip="11.0701",
            year_seed=401_001,
        ),
    )

    econ_sankey = {
        "by_industry_bars": [
            {"label": "Banking / markets", "value": 890},
            {"label": "Consulting", "value": 620},
            {"label": "Government / policy", "value": 410},
            {"label": "Tech", "value": 380},
            {"label": "Other", "value": 720},
        ],
        "nodes": [
            {"id": "e_ra", "label": "Summer internship (research or data)"},
            {"id": "e_analyst", "label": "Analyst — first full-time job"},
            {"id": "e_assoc", "label": "Associate (banking, consulting, etc.)"},
            {"id": "e_vp", "label": "Vice president or principal"},
            {"id": "e_policy", "label": "Policy or graduate-school track"},
            {"id": "e_partner", "label": "Partner or senior director"},
        ],
        "links": [
            {"source": "e_ra", "target": "e_analyst", "value": 520},
            {"source": "e_ra", "target": "e_policy", "value": 180},
            {"source": "e_analyst", "target": "e_assoc", "value": 640},
            {"source": "e_analyst", "target": "e_policy", "value": 120},
            {"source": "e_assoc", "target": "e_vp", "value": 280},
            {"source": "e_assoc", "target": "e_partner", "value": 95},
            {"source": "e_policy", "target": "e_vp", "value": 140},
            {"source": "e_vp", "target": "e_partner", "value": 160},
        ],
    }
    econ_employers = [
        {"label": "Goldman Sachs", "value": 95},
        {"label": "McKinsey", "value": 72},
        {"label": "JPMorgan Chase", "value": 88},
        {"label": "Federal Reserve", "value": 48},
        {"label": "Deloitte", "value": 76},
        {"label": "Other", "value": 1640},
    ]
    write(
        "majors/economics.json",
        major_industry_bundle(
            "economics",
            "Economics, B.A.",
            econ_employers,
            econ_sankey,
            cip="45.0601",
        ),
    )

    bio_sankey = {
        "by_industry_bars": [
            {"label": "Pharma / biotech", "value": 720},
            {"label": "Healthcare providers", "value": 540},
            {"label": "Research / academia", "value": 610},
            {"label": "Other", "value": 430},
        ],
        "nodes": [
            {"id": "b_lab", "label": "Lab tech or research assistant"},
            {"id": "b_assoc_sci", "label": "Associate scientist"},
            {"id": "b_rd", "label": "Industry research scientist"},
            {"id": "b_med", "label": "Medical school or clinical career"},
            {"id": "b_lead", "label": "Science team lead"},
            {"id": "b_pi", "label": "Lead scientist or senior physician"},
        ],
        "links": [
            {"source": "b_lab", "target": "b_assoc_sci", "value": 480},
            {"source": "b_lab", "target": "b_med", "value": 220},
            {"source": "b_assoc_sci", "target": "b_rd", "value": 520},
            {"source": "b_assoc_sci", "target": "b_med", "value": 140},
            {"source": "b_rd", "target": "b_lead", "value": 260},
            {"source": "b_rd", "target": "b_pi", "value": 85},
            {"source": "b_med", "target": "b_pi", "value": 190},
            {"source": "b_lead", "target": "b_pi", "value": 70},
        ],
    }
    bio_employers = [
        {"label": "Pfizer", "value": 62},
        {"label": "UW Health", "value": 118},
        {"label": "AbbVie", "value": 54},
        {"label": "Genentech", "value": 41},
        {"label": "Other", "value": 2025},
    ]
    write(
        "majors/biochemistry.json",
        major_industry_bundle(
            "biochemistry",
            "Biochemistry, B.S.",
            bio_employers,
            bio_sankey,
            cip="26.0202",
            year_seed=403_003,
        ),
    )

    sync_majors_index(OUT / "majors", verbose=True)
    # notable.json: run fetch_wikidata_notable.py (do not overwrite here).

if __name__ == "__main__":
    main()
