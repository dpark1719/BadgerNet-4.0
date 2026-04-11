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
                "top_employers": {
                    "type": "bar",
                    "title": "Top employers (sample, all majors)",
                    "data": [
                        {"label": "Google", "value": 890},
                        {"label": "Epic", "value": 720},
                        {"label": "Microsoft", "value": 610},
                        {"label": "Amazon", "value": 540},
                        {"label": "UW–Madison", "value": 480},
                        {"label": "Deloitte", "value": 390},
                        {"label": "JPMorgan Chase", "value": 340},
                        {"label": "Other / unknown", "value": 12000},
                    ],
                },
                "career_flow": {
                    "type": "sankey",
                    "title": "Synthetic career flow — all majors (early bucket → later bucket)",
                    "nodes": [
                        {"id": "e_intern", "label": "Early — internship"},
                        {"id": "e_entry", "label": "Early — entry IC"},
                        {"id": "m_ic", "label": "Mid — individual contributor"},
                        {"id": "m_mgmt", "label": "Mid — management track"},
                        {"id": "s_lead", "label": "Senior — lead / principal"},
                        {"id": "s_exec", "label": "Senior — exec / founder"},
                    ],
                    "links": [
                        {"source": "e_intern", "target": "e_entry", "value": 2400},
                        {"source": "e_intern", "target": "m_ic", "value": 800},
                        {"source": "e_entry", "target": "m_ic", "value": 3200},
                        {"source": "e_entry", "target": "m_mgmt", "value": 900},
                        {"source": "m_ic", "target": "s_lead", "value": 1400},
                        {"source": "m_ic", "target": "s_exec", "value": 220},
                        {"source": "m_mgmt", "target": "s_exec", "value": 410},
                        {"source": "m_mgmt", "target": "s_lead", "value": 380},
                    ],
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
        "majors/index.json",
        {
            "majors": [
                {
                    "id": "computer_science",
                    "label": "Computer Sciences, B.S.",
                    "cip": "11.0701",
                },
                {
                    "id": "economics",
                    "label": "Economics, B.A.",
                    "cip": "45.0601",
                },
                {
                    "id": "biochemistry",
                    "label": "Biochemistry, B.S.",
                    "cip": "26.0202",
                },
            ]
        },
    )

    def major_industry_bundle(major_id: str, label: str, employers: list, sankey: dict) -> dict:
        return {
            "meta": {
                **common,
                "tab": "industry",
                "major_id": major_id,
                "degree_level": "undergraduate",
                "source": "sample",
                "methodology": (
                    f"Synthetic industry, employer, and career-flow aggregates for major “{label}”. "
                    "Production: LinkedIn harvest rollups by field-of-study filter + aggregation script."
                ),
                "disclaimer": "Not real UW–Madison statistics; major slice for UI development only.",
            },
            "charts": {
                "by_industry": {
                    "type": "bar",
                    "title": f"Alumni by industry — {label} (sample)",
                    "data": sankey["by_industry_bars"],
                },
                "top_employers": {
                    "type": "bar",
                    "title": f"Top employers — {label} (sample)",
                    "data": employers,
                },
                "career_flow": {
                    "type": "sankey",
                    "title": f"Common pathways — {label} (synthetic flow)",
                    "nodes": sankey["nodes"],
                    "links": sankey["links"],
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
            {"id": "cs_intern", "label": "Early — intern (SWE)"},
            {"id": "cs_junior", "label": "Early — junior SWE"},
            {"id": "cs_swe", "label": "Mid — software engineer"},
            {"id": "cs_staff", "label": "Senior — staff / principal"},
            {"id": "cs_pm", "label": "Mid — product / TPM"},
            {"id": "cs_exec", "label": "Senior — exec / founder"},
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
        major_industry_bundle("computer_science", "Computer Sciences, B.S.", cs_employers, cs_sankey),
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
            {"id": "e_ra", "label": "Early — research / analyst intern"},
            {"id": "e_analyst", "label": "Early — analyst"},
            {"id": "e_assoc", "label": "Mid — associate"},
            {"id": "e_vp", "label": "Senior — VP / principal"},
            {"id": "e_policy", "label": "Mid — policy / PhD track"},
            {"id": "e_partner", "label": "Senior — partner / director"},
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
        major_industry_bundle("economics", "Economics, B.A.", econ_employers, econ_sankey),
    )

    bio_sankey = {
        "by_industry_bars": [
            {"label": "Pharma / biotech", "value": 720},
            {"label": "Healthcare providers", "value": 540},
            {"label": "Research / academia", "value": 610},
            {"label": "Other", "value": 430},
        ],
        "nodes": [
            {"id": "b_lab", "label": "Early — lab / RA"},
            {"id": "b_assoc_sci", "label": "Early — associate scientist"},
            {"id": "b_rd", "label": "Mid — R&D scientist"},
            {"id": "b_med", "label": "Mid — med school / clinician track"},
            {"id": "b_lead", "label": "Senior — team lead"},
            {"id": "b_pi", "label": "Senior — PI / medical lead"},
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
        major_industry_bundle("biochemistry", "Biochemistry, B.S.", bio_employers, bio_sankey),
    )

    write(
        "notable.json",
        {
            "meta": {
                **common,
                "tab": "notable_alumni",
                "degree_level": "all",
                "source": "mixed",
                "methodology": (
                    "Sample entries mix illustrative public figures and synthetic “senior role” placeholders. "
                    "Production: Wikidata SPARQL (educated at UW–Madison), UW news, and reviewed LinkedIn-aggregate flags. "
                    "Every row requires source_url."
                ),
                "disclaimer": (
                    "Not an official UW ranking. Inclusion is for illustration; verify via linked sources. "
                    "LinkedIn-derived rows must be reviewed before publication."
                ),
            },
            "entries": [
                {
                    "name": "Charles Lindbergh",
                    "role_title": "Aviator (attended engineering, did not graduate)",
                    "organization": "—",
                    "notability": "widely_cited",
                    "source_url": "https://en.wikipedia.org/wiki/Charles_Lindbergh",
                    "source_type": "wikipedia",
                    "year": "1920s attendance",
                },
                {
                    "name": "Frank Lloyd Wright",
                    "role_title": "Architect (attended, did not graduate)",
                    "organization": "—",
                    "notability": "widely_cited",
                    "source_url": "https://en.wikipedia.org/wiki/Frank_Lloyd_Wright",
                    "source_type": "wikipedia",
                },
                {
                    "name": "Sample placeholder — CEO",
                    "role_title": "Chief Executive Officer (synthetic)",
                    "organization": "Example Corp",
                    "notability": "senior_role",
                    "source_url": "https://github.com/dpark1719/BadgerNet-4.0",
                    "source_type": "other",
                },
            ],
        },
    )

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
                "This app loads static JSON from /data. Seven top-level tabs including Notable alumni. "
                "Industry supports a major filter (see /data/majors/). Career flow uses sankey aggregates; "
                "top employers use bar charts. Notable list requires source_url per row (Wikidata, news, reviewed LinkedIn)."
            ),
            "tabs": [
                {"id": "industry", "label": "Industry"},
                {"id": "postgrad", "label": "Post-grad education"},
                {"id": "international", "label": "International outcomes"},
                {"id": "origins_undergrad", "label": "Origins — Undergraduate"},
                {"id": "origins_graduate", "label": "Origins — Graduate"},
                {"id": "origins_doctorate", "label": "Origins — Doctorate"},
                {"id": "notable_alumni", "label": "Notable alumni"},
            ],
        },
    )


if __name__ == "__main__":
    main()
