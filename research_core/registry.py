from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


REQUIRED_SOURCE_FIELDS = {"id", "category", "name", "class", "role", "ingest_status"}


def validate_source_registry(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    errors: list[str] = []
    warnings: list[str] = []

    canonical = payload.get("canonical_map")
    if not canonical:
        errors.append("canonical_map missing")
    else:
        canonical_path = path.parent.parent / canonical
        if not canonical_path.exists():
            errors.append(f"canonical_map does not exist: {canonical_path}")

    sources = payload.get("sources")
    if not isinstance(sources, list):
        errors.append("sources must be a list")
        sources = []

    ids: set[str] = set()
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            errors.append(f"source #{index} is not an object")
            continue
        missing = REQUIRED_SOURCE_FIELDS - source.keys()
        if missing:
            errors.append(f"source #{index} missing fields: {sorted(missing)}")
        source_id = source.get("id")
        if source_id:
            if source_id in ids:
                errors.append(f"duplicate source id: {source_id}")
            ids.add(source_id)
        if source.get("class") in {"market_data", "market_data_web", "macro_event_data", "macro_event_calendar"} and not source.get("url"):
            warnings.append(f"data source has no URL: {source_id}")

    return {
        "status": "fail" if errors else ("pass_with_warnings" if warnings else "pass"),
        "sources": len(sources),
        "errors": errors,
        "warnings": warnings,
    }
