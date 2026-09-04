from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research_core.mt5_utc_bundle import sha256_file, validate_utc_bundle_manifest


UTC = timezone.utc
EXPECTED_EXPORTER_ID = "p_mt5_utc_bundle_v1"
MAJOR_SESSION_POLICY_ID = "xauusd_major_fx_sessions_v1"


def _slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    if not text:
        raise ValueError("cannot derive dataset id from empty symbol")
    return text


def _parse_utc_timestamp(value: Any) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise ValueError("export_time_utc is required")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("export_time_utc must be valid ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("export_time_utc must be timezone-aware")
    parsed_utc = parsed.astimezone(UTC)
    if parsed_utc.utcoffset() != timezone.utc.utcoffset(parsed_utc):
        raise ValueError("export_time_utc must normalize to UTC")
    return parsed_utc


def canonical_dataset_id(manifest: dict[str, Any]) -> str:
    symbol = manifest.get("symbol")
    if not isinstance(symbol, dict) or not str(symbol.get("name", "")).strip():
        raise ValueError("symbol.name is required")
    export_time = _parse_utc_timestamp(manifest.get("export_time_utc"))
    stamp = export_time.strftime("%Y%m%d_%H%M%S")
    return f"{_slug(str(symbol['name']))}_mt5_utc_{stamp}"


def build_promotion_record(manifest_path: str | Path) -> dict[str, Any]:
    path = Path(manifest_path).expanduser().resolve()
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("binding manifest must contain a JSON object")

    validation = validate_utc_bundle_manifest(manifest, path.parent)
    if validation["status"] == "fail":
        raise ValueError("binding manifest validation failed: " + "; ".join(validation["errors"]))

    exporter = manifest.get("exporter")
    if not isinstance(exporter, dict) or exporter.get("id") != EXPECTED_EXPORTER_ID:
        raise ValueError(f"exporter.id must be {EXPECTED_EXPORTER_ID}")

    broker = manifest.get("broker")
    if not isinstance(broker, dict):
        raise ValueError("broker metadata missing")
    company = str(broker.get("company", "")).strip()
    server = str(broker.get("server", "")).strip()
    if not company or not server:
        raise ValueError("broker company/server are required")

    symbol = manifest.get("symbol")
    if not isinstance(symbol, dict):
        raise ValueError("symbol metadata missing")
    symbol_name = str(symbol.get("name", "")).strip()
    if not symbol_name:
        raise ValueError("symbol.name is required")

    export_time = _parse_utc_timestamp(manifest.get("export_time_utc"))
    dataset_id = canonical_dataset_id(manifest)

    files: list[dict[str, Any]] = []
    for item in manifest.get("files", []):
        files.append(
            {
                "path": item.get("path"),
                "kind": item.get("kind"),
                "timeframe": item.get("timeframe"),
                "rows": item.get("rows"),
                "first_time_utc": item.get("first_time_utc"),
                "last_time_utc": item.get("last_time_utc"),
                "sha256": item.get("sha256"),
            }
        )

    return {
        "schema_version": 1,
        "dataset_id": dataset_id,
        "source_id": "user_mt5_export",
        "market": "xauusd",
        "symbol": symbol_name,
        "status": "verified",
        "timebase": {
            "timestamp_semantics": "utc_from_metatrader5_python_api",
            "source_timezone": "UTC",
            "dst_policy": "not_applicable_input_already_utc",
            "broker_feed_identity": f"{company} / {server} / {symbol_name}",
            "named_session_use_allowed": True,
        },
        "session_policy_authorization": {
            "eligible": True,
            "requires_verified_utc": True,
            "policy_id": MAJOR_SESSION_POLICY_ID,
            "note": "Authorization is for research-session classification only; it does not imply a trading signal.",
        },
        "provenance": {
            "binding_manifest_filename": path.name,
            "binding_manifest_sha256": sha256_file(path),
            "export_time_utc": export_time.isoformat(),
            "exporter_id": exporter.get("id"),
            "exporter_version": exporter.get("version"),
            "broker_company": company,
            "broker_server": server,
            "terminal": manifest.get("terminal"),
            "binding_scope": manifest.get("binding_scope"),
            "legacy_source_local_bundle_retroactively_verified": manifest.get(
                "legacy_source_local_bundle_retroactively_verified"
            ),
        },
        "files": files,
        "validation": validation,
    }
