"""Helpers for notable alumni: Wikipedia thumbnails, Commons image URLs, achievement badges."""

from __future__ import annotations

import re
import time
import urllib.parse
from typing import Any

UA = (
    "BadgerNet4/1.0 (https://github.com/dpark1719/BadgerNet-4.0; notable alumni enrichment)"
)

# Relative to site root (Vite public/) — resolved by frontend publicPath()
BADGE_NOBEL = ("notable/badge-nobel.svg", "Nobel Prize")
BADGE_PULITZER = ("notable/badge-pulitzer.svg", "Pulitzer Prize")
BADGE_OLYMPIC = ("notable/badge-olympic.svg", "Olympic Games")
BADGE_OSCAR = ("notable/badge-arts.svg", "Academy Award")
BADGE_FOUNDER = ("notable/badge-founder.svg", "Founder / entrepreneur")
BADGE_EXEC = ("notable/badge-exec.svg", "Executive leadership")
BADGE_ARCHITECTURE = ("notable/badge-architecture.svg", "Architecture")
BADGE_AVIATION = ("notable/badge-aviation.svg", "Aviation")
BADGE_COMPANY = ("notable/company-generic.svg", "Organization")


def commons_image_thumb(uri: str, width: int = 128) -> str:
    """Add width query to Commons Special:FilePath or pass through upload.wikimedia.org thumbs."""
    u = uri.strip()
    if "Special:FilePath" in u or "special:filepath" in u.lower():
        sep = "&" if "?" in u else "?"
        if "width=" not in u.lower():
            return f"{u}{sep}width={width}"
    return u


def wikipedia_title_from_en_url(url: str) -> str | None:
    m = re.search(
        r"(?:https?://)?en\.wikipedia\.org/wiki/([^#?]+)", url.strip(), re.I
    )
    if not m:
        return None
    return urllib.parse.unquote(m.group(1))


def fetch_wikipedia_summary(
    session: Any, article_url: str, pause_s: float = 0.0
) -> dict[str, Any] | None:
    """REST summary: thumbnail, description, extract. Returns None on failure."""
    title = wikipedia_title_from_en_url(article_url)
    if not title:
        return None
    api_title = title.replace(" ", "_")
    encoded = urllib.parse.quote(api_title, safe="()%")
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
    if pause_s > 0:
        time.sleep(pause_s)
    r = session.get(url, headers={"User-Agent": UA}, timeout=25)
    if r.status_code != 200:
        return None
    try:
        return r.json()
    except Exception:
        return None


def short_bio_from_summary(summary: dict[str, Any], max_chars: int = 260) -> str | None:
    """
    One-line Wikidata-style `description`, or first plain-text chunk of `extract`.
    Suitable for alumni card subtitle (replaces generic 'Notable person' text).
    """
    d = summary.get("description")
    if isinstance(d, str):
        t = d.strip()
        if len(t) > 3:
            return t[:max_chars] + ("…" if len(t) > max_chars else "")

    ext = summary.get("extract")
    if not isinstance(ext, str):
        return None
    text = re.sub(r"<[^>]+>", " ", ext)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return None
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    last_period = cut.rfind(". ")
    last_space = cut.rfind(" ")
    if last_period >= 80:
        return cut[: last_period + 1].strip()
    if last_space >= 60:
        return cut[:last_space].strip() + "…"
    return cut.rstrip() + "…"


def photo_url_from_summary(summary: dict[str, Any]) -> str | None:
    t = summary.get("thumbnail") or summary.get("originalimage")
    if isinstance(t, dict):
        src = t.get("source")
        if isinstance(src, str) and src.startswith("http"):
            return src
    return None


def infer_achievement_from_text(
    role_title: str, organization: str, summary: dict[str, Any] | None
) -> tuple[str | None, str | None]:
    """
    Returns (achievement_image_url, achievement_label) using public-relative paths.
    """
    parts = [role_title or "", organization or ""]
    if summary:
        parts.append(summary.get("description") or "")
        parts.append(summary.get("extract") or "")
    text = " ".join(parts).lower()

    if "nobel" in text:
        return BADGE_NOBEL
    if "pulitzer" in text:
        return BADGE_PULITZER
    if "olympic" in text or "olympian" in text:
        return BADGE_OLYMPIC
    if "oscar" in text or "academy award" in text:
        return BADGE_OSCAR
    if any(
        w in text
        for w in ("founder", "co-founder", "cofounder", "co founder", "entrepreneur")
    ):
        return BADGE_FOUNDER
    if re.search(r"\bceo\b", text) or "chief executive" in text:
        return BADGE_EXEC
    if "architect" in text or "architecture" in text:
        return BADGE_ARCHITECTURE
    if "aviat" in text or "pilot" in text or "aviation" in text:
        return BADGE_AVIATION
    org = (organization or "").strip()
    if org and org not in ("—", "-", "–", "n/a", "N/A"):
        return BADGE_COMPANY
    return (None, None)
