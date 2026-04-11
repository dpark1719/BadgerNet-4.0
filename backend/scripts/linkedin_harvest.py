#!/usr/bin/env python3
"""
LinkedIn aggregate harvest — **stub** (no API; browser automation TBD).

Policy for the real implementation:
- Log in with a **dedicated** account; store session via Playwright ``storage_state`` path from env.
- Collect **aggregates only** (counts / facet summaries), not profile-level exports.
- Respect conservative rate limits; run infrequently.
- Write rollups into ``frontend/public/data/*.json`` with ``meta.filter_fingerprint`` and ``meta.methodology``.

Dependencies (when you implement): ``playwright`` + ``pip install playwright && playwright install chromium``

Environment (see backend/.env.example):
- ``LINKEDIN_STORAGE_STATE`` — path to saved storage JSON (local, never commit)

This script only documents the approach and exits.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    state = os.environ.get("LINKEDIN_STORAGE_STATE", "")
    print("BadgerNet — LinkedIn harvest stub (automation not enabled in repo)")
    print(f"  Repo root: {ROOT}")
    if state:
        print(f"  LINKEDIN_STORAGE_STATE is set ({state[:20]}…); implement Playwright flow next.")
    else:
        print("  Set LINKEDIN_STORAGE_STATE in .env after saving a logged-in storage state.")
    print("  Do not commit credentials, storage state, or raw HTML.")
    sys.exit(0)


if __name__ == "__main__":
    main()
