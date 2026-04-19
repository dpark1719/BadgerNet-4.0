"""Deterministic per-year splits for multi-cohort demo data (2016–2025)."""

from __future__ import annotations

import random

YEARS = list(range(2016, 2026))


def split_total_by_year(total: int, seed: int) -> dict[str, int]:
    rng = random.Random(seed & 0xFFFFFFFF)
    n = len(YEARS)
    if total <= 0:
        return {str(y): 0 for y in YEARS}
    weights = [rng.random() + 0.25 for _ in range(n)]
    s = sum(weights)
    floats = [total * w / s for w in weights]
    ints = [int(x) for x in floats]
    diff = total - sum(ints)
    i = 0
    while diff > 0:
        ints[i % n] += 1
        diff -= 1
        i += 1
    return {str(y): v for y, v in zip(YEARS, ints)}


def bar_row(label: str, value: int, seed: int) -> dict:
    return {"label": label, "value": value, "by_year": split_total_by_year(value, seed)}


def bars_with_years(rows: list[dict], seed: int) -> list[dict]:
    return [
        bar_row(r["label"], int(r["value"]), seed + i * 31) for i, r in enumerate(rows)
    ]


def sankey_links_with_years(links: list[dict], seed: int) -> list[dict]:
    out: list[dict] = []
    for i, L in enumerate(links):
        v = int(L["value"])
        out.append(
            {
                **L,
                "value": v,
                "by_year": split_total_by_year(v, seed + i * 47),
            }
        )
    return out


def pct_by_year(center: float, seed: int) -> dict[str, float]:
    rng = random.Random(seed & 0xFFFFFFFF)
    raw: list[float] = []
    for _ in YEARS:
        raw.append(max(0.0, min(100.0, center + (rng.random() - 0.5) * 6.0)))
    adj = center - sum(raw) / len(raw)
    adjusted = [round(max(0.0, min(100.0, v + adj)), 2) for v in raw]
    drift = center - sum(adjusted) / len(adjusted)
    adjusted[-1] = round(
        max(0.0, min(100.0, adjusted[-1] + drift * len(adjusted))),
        2,
    )
    return {str(y): adjusted[i] for i, y in enumerate(YEARS)}
