#!/usr/bin/env python3
"""
LinkedIn **aggregate** harvest template (Playwright).

Prerequisites:
  pip install playwright
  playwright install chromium

Setup:
  1. Copy backend/.env.example to backend/.env
  2. Log in to LinkedIn once in a normal browser; or use Playwright codegen to
     save storage state to LINKEDIN_STORAGE_STATE (JSON).

This file does **not** ship working selectors — LinkedIn UI changes frequently.
Implement navigation to the UW school alumni page, apply filters, and read
**counts or facet text** from the DOM; write CSV for linkedin_aggregate_to_majors.py.

Run:
  python linkedin_playwright_harvest.py --dry-run   # prints steps only
"""

from __future__ import annotations

import argparse
import os
import sys


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    state = os.environ.get("LINKEDIN_STORAGE_STATE", "")
    if args.dry_run:
        print("Dry run — no browser launched.")
        print("  LINKEDIN_STORAGE_STATE:", state or "(not set)")
        print("  Next: implement page.goto + locator text for aggregate counts.")
        print("  Output: CSV for linkedin_aggregate_to_majors.py")
        return

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Install: pip install playwright && playwright install chromium")
        sys.exit(1)

    if not state or not os.path.isfile(state):
        print("Set LINKEDIN_STORAGE_STATE to a saved storage_state.json path.")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(storage_state=state)
        page = context.new_page()
        page.goto("https://www.linkedin.com/school/university-of-wisconsin-madison/", timeout=60000)
        print("Page title:", page.title())
        print("Implement DOM scraping here; do not commit raw HTML.")
        browser.close()


if __name__ == "__main__":
    main()
