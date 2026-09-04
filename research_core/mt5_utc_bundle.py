from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


UTC = timezone.utc
REQUIRED_MANIFEST_FIELDS = {
    "schema_version",
    "exporter",
    "timestamp_semantics",
    "export_time_utc",
    "broker",
    "symbol",
    "files",
}


def epoch_seconds_to_utc_iso(value: int | float) -> str:
    return datetime.fromtimestamp(float(value), tz=UTC).isoformat().replace("+00:00", "Z")


def epoch_milliseconds_to_utc_iso(value: int | float) -> str:
    return datetime.fromtimestamp(float(value) / 1000.0, tz=UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def bar_is_closed(open_epoch_seconds: int | float, timeframe_seconds: int, cutoff_epoch_seconds: int | float) -> bool:
    if timeframe_seconds <= 0:
        raise ValueError("timeframe_seconds must be positive")
    return float(open_epoch_seconds) + int(timeframe_seconds) <= float(cutoff_epoch_seconds)


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_utc_bundle_manifest(manifest: dict[str, Any], base_dir: str | Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    missing = REQUIRED_MANIFEST_FIELDS - manifest.keys()
    if missing:
        errors.append(f"missing manifest fields: {sorted(missing)}")

    semantics = manifest.get("timestamp_semantics")
    if semantics != "utc_from_metatrader5_python_api":
        errors.append("timestamp_semantics must be utc_from_metatrader5_python_api")

    broker = manifest.get("broker")
    if not isinstance(broker, dict):
        errors.append("broker must be an object")
    else:
        if not broker.get("company"):
            errors.append("broker.company missing")
        if not broker.get("server"):
            errors.append("broker.server missing")

    symbol = manifest.get("symbol")
    if not isinstance(symbol, dict) or not symbol.get("name"):
        errors.append("symbol.name missing")

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        errors.append("files must be a non-empty list")
        files = []

    root = Path(base_dir)
    for index, item in enumerate(files, start=1):
        if not isinstance(item, dict):
            errors.append(f"file #{index} is not an object")
            continue
        rel = item.get("path")
        expected_hash = item.get("sha256")
        rows = item.get("rows")
        if not rel or not expected_hash:
            errors.append(f"file #{index} missing path/sha256")
            continue
        if not isinstance(rows, int) or rows < 0:
            errors.append(f"file #{index} rows must be a non-negative integer")
        path = root / rel
        if not path.exists():
            errors.append(f"missing file: {rel}")
            continue
        observed_hash = sha256_file(path)
        if observed_hash != expected_hash:
            errors.append(f"sha256 mismatch: {rel}")

    if manifest.get("legacy_source_local_bundle_retroactively_verified") is True:
        errors.append("canonical UTC export must not retroactively verify legacy source-local bundles")

    status = "fail" if errors else ("pass_with_warnings" if warnings else "pass")
    return {"status": status, "errors": errors, "warnings": warnings}
