from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .data_validation import read_csv_rows, extract_timestamp


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def inspect_csv_time_range(path: str | Path) -> tuple[int, str | None, str | None]:
    rows, _ = read_csv_rows(path)
    timestamps = []
    for row in rows:
        try:
            timestamps.append(extract_timestamp(row))
        except Exception:
            continue
    return (
        len(rows),
        min(timestamps).isoformat() if timestamps else None,
        max(timestamps).isoformat() if timestamps else None,
    )


def build_dataset_manifest(
    path: str | Path,
    *,
    source_id: str,
    market: str,
    symbol: str,
    data_type: str,
    timezone_name: str,
    timeframe: str | None = None,
    normalization_timezone: str | None = None,
    analysis_cutoff: str | None = None,
    forming_bar_policy: str | None = None,
) -> dict[str, Any]:
    path = Path(path)
    rows, start_ts, end_ts = inspect_csv_time_range(path)
    dataset_id = f"{market}_{source_id}_{data_type}_{path.stem}".lower().replace(" ", "_")
    return {
        "dataset_id": dataset_id,
        "market": market,
        "symbol": symbol,
        "source_id": source_id,
        "data_type": data_type,
        "timeframe": timeframe,
        "timezone": timezone_name,
        "normalization_timezone": normalization_timezone,
        "start_timestamp": start_ts,
        "end_timestamp": end_ts,
        "analysis_cutoff": analysis_cutoff,
        "forming_bar_policy": forming_bar_policy,
        "file_path": str(path),
        "sha256": sha256_file(path),
        "rows": rows,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "validation": {"status": "not_run", "errors": 0, "warnings": 0, "validator": None},
    }


def write_manifest(manifest: dict[str, Any], output_path: str | Path) -> None:
    Path(output_path).write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
