#!/usr/bin/env python3
"""Deprecated entry name — use build_origins_ipeds.py."""

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    subprocess.run([sys.executable, str(here / "build_origins_ipeds.py")] + sys.argv[1:], check=True)
