#!/usr/bin/env python3
"""
Regenerate frontend/public/data/majors/index.json from slice files majors/*.json.

Include every slice (except index.json) with a non-empty `charts` object.
Labels merge: existing index row → meta.major_display_name / major_label → humanized id.

Run after adding or removing major JSON by hand, or rely on linkedin_aggregate_to_majors.py
(which calls this automatically).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.lib.majors_index import DEFAULT_MAJORS_DIR, sync_majors_index  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--majors-dir",
        type=Path,
        default=None,
        help=f"Default: {DEFAULT_MAJORS_DIR}",
    )
    ap.add_argument("-q", "--quiet", action="store_true")
    args = ap.parse_args()
    sync_majors_index(args.majors_dir, verbose=not args.quiet)


if __name__ == "__main__":
    main()
