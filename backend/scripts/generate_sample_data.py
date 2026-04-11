#!/usr/bin/env python3
"""Emit chart JSON bundles for the frontend (sample / dev data)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "frontend" / "public" / "data"


def write(name: str, payload: object) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT)}")


def main() -> None:
    common = {
        "project": "BadgerNet 4.0",
        "snapshot_date": "2026-04-11",
        "academic_year": "2023-24",
    }

    write(
        "industry.json",
        {
            "meta": {
                **common,
                "tab": "industry",
                "degree_level": "all",
                "source": "sample",
                "source_url": None,
                "methodology": "Synthetic counts for UI development. Replace with UW survey + LinkedIn rollups.",
                "disclaimer": "Not real UW–Madison statistics.",
            },
            "charts": {
                "by_industry": {
                    "type": "bar",
                    "title": "Alumni by industry (sample)",
                    "data": [
                        {"label": "Technology", "value": 4200},
                        {"label": "Healthcare", "value": 3100},
                        {"label": "Finance", "value": 2400},
                        {"label": "Education", "value": 1900},
                        {"label": "Manufacturing", "value": 1200},
                        {"label": "Other", "value": 2800},
                    ],
                }
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
                "methodology": "Synthetic continuation rate and degree-type mix.",
                "disclaimer": "Not from an official first-destination survey.",
            },
            "charts": {
                "continuation_rate": {
                    "type": "metric",
                    "title": "Continuing formal education within 1 year (sample)",
                    "value": 22.4,
                    "unit": "percent",
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
                "methodology": "Synthetic destination-country mix; production data may be LinkedIn-filtered aggregates.",
                "disclaimer": "International ‘where they go’ is often incomplete in official sources; any LinkedIn layer is a biased sample.",
            },
            "charts": {
                "destination_country": {
                    "type": "bar",
                    "title": "Post-UW country — sample proxy",
                    "data": [
                        {"label": "United States", "value": 450},
                        {"label": "India", "value": 180},
                        {"label": "China", "value": 120},
                        {"label": "South Korea", "value": 55},
                        {"label": "Canada", "value": 48},
                        {"label": "Other", "value": 210},
                    ],
                }
            },
        },
    )

    write(
        "origins.json",
        {
            "meta": {
                **common,
                "tab": "origins",
                "degree_level": "undergraduate",
                "source": "sample",
                "methodology": "Synthetic US state + country origin; production should use IPEDS / CDS enrollment.",
                "disclaimer": "Degree level can be toggled in UI; ensure backend emits matching slices.",
            },
            "charts": {
                "us_states": {
                    "type": "bar",
                    "title": "US home state — enrolled (sample, UG)",
                    "data": [
                        {"label": "Wisconsin", "value": 8200},
                        {"label": "Illinois", "value": 2100},
                        {"label": "Minnesota", "value": 980},
                        {"label": "California", "value": 720},
                        {"label": "Other", "value": 5400},
                    ],
                },
                "countries": {
                    "type": "bar",
                    "title": "Country of origin — international enrolled (sample)",
                    "data": [
                        {"label": "China", "value": 1200},
                        {"label": "India", "value": 890},
                        {"label": "South Korea", "value": 410},
                        {"label": "Canada", "value": 260},
                        {"label": "Other", "value": 1500},
                    ],
                },
            },
        },
    )

    write(
        "meta.json",
        {
            "site": {
                "name": "BadgerNet 4.0",
                "tagline": "Where UW–Madison students and alumni go — data-driven views (in progress).",
            },
            "github_project": "https://github.com/users/dpark1719/projects/2",
            "methodology_blurb": (
                "This MVP loads static JSON from /data. Industry and international outcomes may later combine "
                "UW-published reports with aggregated LinkedIn signals. Origins should track IPEDS/CDS enrollment. "
                "Every chart should cite its source and display disclaimers where samples are biased or incomplete."
            ),
            "tabs": [
                {"id": "industry", "label": "Industry"},
                {"id": "postgrad", "label": "Post-grad education"},
                {"id": "international", "label": "International outcomes"},
                {"id": "origins", "label": "Student origins"},
            ],
        },
    )


if __name__ == "__main__":
    main()
