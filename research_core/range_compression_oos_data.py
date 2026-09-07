from __future__ import annotations

import csv
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import yaml
from .session_policy import NamedSessionPolicy
from pathlib import Path
from typing import Any

from .mt5_utc_bundle import sha256_file, validate_utc_bundle_manifest

START = "2026-09-08"
UTC = timezone.utc


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware UTC")
    return parsed.astimezone(UTC)


def _eligible_reference_sessions(rows, root: Path):
    repo_root = Path(__file__).resolve().parents[1]
    strategy_path = repo_root / "quant" / "candidates" / "XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.strategy.yaml"
    strategy = yaml.safe_load(strategy_path.read_text(encoding="utf-8"))
    policy = NamedSessionPolicy.from_yaml(repo_root / str(strategy["session_context"]["policy_path"]))
    zone = ZoneInfo(policy.definitions["new_york"].timezone_name)
    by_ts = {_utc(row["time_utc"]): row for row in rows}
    expected_ny_bars = int(yaml.safe_load((repo_root / "quant" / "candidates" / "XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.evaluation.yaml").read_text(encoding="utf-8"))["data"]["expected_new_york_m5_bars"])
    interval = timedelta(minutes=5)
    timestamps = sorted(by_ts)
    if not timestamps:
        return []
    first = timestamps[0].astimezone(zone).date() - timedelta(days=1)
    last = timestamps[-1].astimezone(zone).date() + timedelta(days=1)
    result = []
    current = first
    while current <= last:
        if current.weekday() in policy.definitions["new_york"].weekdays:
            ny_start, ny_end = policy.bounds_utc("new_york", current)
            if ny_end > timestamps[-1] or ny_start < timestamps[0]:
                current += timedelta(days=1)
                continue
            ny_opens = [ny_start + interval*i for i in range(expected_ny_bars)]
            if len(ny_opens) != expected_ny_bars or any(ts not in by_ts or str(by_ts[ts].get("is_closed", "")).lower() not in {"true", "1"} for ts in ny_opens):
                current += timedelta(days=1)
                continue
            ref_start = ny_start - timedelta(minutes=int(strategy["baseline_parameters"]["pre_ny_reference_minutes"]))
            opens = [ref_start + timedelta(minutes=5*i) for i in range(int(strategy["reference_range"]["expected_m5_bars"]))]
            if len(opens) == 48 and all(ts in by_ts for ts in opens) and all(str(by_ts[ts].get("is_closed", "")).lower() in {"true", "1"} for ts in opens) and all(policy.contains("london", ts) for ts in opens):
                bars = [by_ts[ts] for ts in opens]
                high = max(float(row["high"]) for row in bars)
                low = min(float(row["low"]) for row in bars)
                if high > low:
                    result.append({"session_date": current.isoformat(), "reference_high": high, "reference_low": low, "current_reference_width": high-low})
        current += timedelta(days=1)
    return result
def prepare_oos_data(manifest_path: str | Path, *, prospective_start: str = START) -> dict[str, Any]:
    if prospective_start != START:
        raise ValueError("prospective start session is immutable at 2026-09-08")
    path = Path(manifest_path).expanduser().resolve()
    root = path.parent
    errors: list[str] = []
    warnings: list[str] = []
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        validation = validate_utc_bundle_manifest(manifest, root)
        errors.extend(validation["errors"])
        warnings.extend(validation["warnings"])
    except Exception as exc:
        return {"status": "not_ready", "manifest_path": str(path), "performance_evaluated": False, "errors": [str(exc)], "warnings": []}
    symbol = manifest.get("symbol", {}).get("name") if isinstance(manifest.get("symbol"), dict) else None
    if symbol != "XAUUSD_o":
        errors.append("symbol must match XAUUSD_o")
    files = manifest.get("files", [])
    m5 = next((item for item in files if isinstance(item, dict) and item.get("kind") == "ohlc" and str(item.get("timeframe", "")).upper() == "M5"), None)
    if m5 is None:
        errors.append("canonical M5 file is missing from manifest")
    rows: list[dict[str, Any]] = []
    duplicate_count = 0
    ordered = True
    ohlc_valid = True
    forming = 0
    if m5 is not None:
        m5_path = root / str(m5["path"])
        try:
            with m5_path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            previous = None
            seen = set()
            for row in rows:
                ts = _utc(row["time_utc"])
                if ts in seen:
                    duplicate_count += 1
                seen.add(ts)
                if previous is not None and ts <= previous:
                    ordered = False
                previous = ts
                values = [float(row[field]) for field in ("open", "high", "low", "close")]
                if values[1] < max(values[0], values[3]) or values[2] > min(values[0], values[3]) or values[1] < values[2]:
                    ohlc_valid = False
                if str(row.get("is_closed", "")).lower() not in {"true", "1"}:
                    forming += 1
        except Exception as exc:
            errors.append(f"unable to inspect canonical M5: {exc}")
    closed_rows = len(rows) - forming
    first_closed = next((row["time_utc"] for row in rows if str(row.get("is_closed", "")).lower() in {"true", "1"}), None)
    closed_reversed = list(reversed(rows))
    last_closed = next((row["time_utc"] for row in closed_reversed if str(row.get("is_closed", "")).lower() in {"true", "1"}), None)
    if duplicate_count:
        errors.append("duplicate M5 timestamps detected")
    if not ordered:
        errors.append("M5 timestamps are not strictly ordered")
    if not ohlc_valid:
        errors.append("invalid M5 OHLC detected")
    eligible = _eligible_reference_sessions(rows, root) if rows and m5 is not None else []
    pre_oos_eligible = [item for item in eligible if item["session_date"] < prospective_start]
    pre_history = len(pre_oos_eligible) >= 20
    prospective_sessions = [item["session_date"] for item in eligible if item["session_date"] >= prospective_start]
    prospective_present = bool(prospective_sessions)
    if not pre_history:
        errors.append("insufficient pre-OOS historical state coverage")
    if m5 is not None and len(rows) < int(m5.get("rows", len(rows))):
        warnings.append("observed M5 rows are fewer than manifest declaration")
    result = {"status": "not_ready" if errors else "ready", "dataset_id": manifest.get("dataset_id"), "symbol": symbol, "manifest_path": str(path), "manifest_sha256": sha256_file(path), "m5_path": str(root / str(m5["path"])) if m5 else None, "m5_sha256": m5.get("sha256") if m5 else None, "first_closed_m5_utc": first_closed, "last_closed_m5_utc": last_closed, "closed_m5_rows": closed_rows, "forming_m5_rows": forming, "duplicate_m5_timestamps": duplicate_count, "ordered": ordered, "ohlc_valid": ohlc_valid, "prospective_start_session": prospective_start, "historical_state_sessions_required": 20, "eligible_pre_oos_reference_sessions": len(pre_oos_eligible), "historical_state_sessions_missing": max(0, 20-len(pre_oos_eligible)), "pre_oos_history_available": pre_history, "prospective_data_present": prospective_present, "prospective_complete_session_present": prospective_present, "performance_evaluated": False, "errors": errors, "warnings": warnings}
    return result
