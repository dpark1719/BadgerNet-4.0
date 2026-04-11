#!/usr/bin/env python3
"""Deprecated stub — use linkedin_playwright_harvest.py and linkedin_aggregate_to_majors.py."""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    print("Use: python3 backend/scripts/linkedin_playwright_harvest.py --dry-run")
    subprocess.run([sys.executable, str(here / "linkedin_playwright_harvest.py"), "--dry-run"])
