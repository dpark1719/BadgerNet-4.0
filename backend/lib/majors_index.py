"""Build majors/index.json from per-major slice files under public/data/majors/."""

from __future__ import annotations

import json
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MAJORS_DIR = _REPO_ROOT / "frontend" / "public" / "data" / "majors"


def humanize_major_id(stem: str) -> str:
    return stem.replace("_", " ").strip().title()


def _slice_has_charts(data: dict) -> bool:
    charts = data.get("charts")
    return isinstance(charts, dict) and len(charts) > 0


def _load_previous_index(index_path: Path) -> dict[str, dict]:
    if not index_path.is_file():
        return {}
    try:
        raw = json.loads(index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    out: dict[str, dict] = {}
    for row in raw.get("majors") or []:
        if not isinstance(row, dict):
            continue
        mid = (row.get("id") or "").strip()
        if not mid:
            continue
        out[mid] = {
            "label": (row.get("label") or "").strip(),
            "cip": (row.get("cip") or "").strip() or None,
        }
    return out


def sync_majors_index(
    majors_dir: Path | None = None,
    *,
    index_name: str = "index.json",
    verbose: bool = True,
) -> dict:
    """
    Scan majors_dir for *.json except index_name; include slices with non-empty charts.
    Merge labels/CIP from existing index.json, then meta.major_display_name / major_label,
    meta.major_cip / cip, else humanized filename stem for label.
    Returns the written payload {"majors": [...]}.
    """
    root = majors_dir or DEFAULT_MAJORS_DIR
    index_path = root / index_name
    prev = _load_previous_index(index_path)

    rows: list[dict] = []
    for path in sorted(root.glob("*.json")):
        if path.name == index_name:
            continue
        stem = path.stem
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            if verbose:
                print(f"Skip {path.name}: {e}")
            continue
        if not _slice_has_charts(data):
            if verbose:
                print(f"Skip {path.name}: empty charts")
            continue
        meta = data.get("meta") if isinstance(data.get("meta"), dict) else {}
        mid_meta = (meta.get("major_id") or "").strip()
        if mid_meta and mid_meta != stem:
            print(
                f"Warning: {path.name} meta.major_id={mid_meta!r} != filename stem {stem!r}; using stem as id"
            )

        prev_row = prev.get(stem, {})
        label = (prev_row.get("label") or "").strip()
        cip_val = prev_row.get("cip")

        if not label:
            label = (
                (meta.get("major_display_name") or meta.get("major_label") or "").strip()
            )
        if not label:
            label = humanize_major_id(stem)

        cip_out = (cip_val or "").strip() if cip_val else ""
        if not cip_out:
            cip_out = (meta.get("major_cip") or meta.get("cip") or "").strip()

        entry: dict = {"id": stem, "label": label}
        if cip_out:
            entry["cip"] = cip_out
        rows.append(entry)

    rows.sort(key=lambda r: (r["label"].lower(), r["id"]))
    payload = {"majors": rows}
    root.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if verbose:
        try:
            rel = index_path.relative_to(_REPO_ROOT)
        except ValueError:
            rel = index_path
        print(f"Wrote {rel} ({len(rows)} majors)")
    return payload
