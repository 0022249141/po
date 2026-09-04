#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from research_core.mt5_utc_bundle import (
    bar_is_closed,
    epoch_milliseconds_to_utc_iso,
    epoch_seconds_to_utc_iso,
    sha256_file,
)


UTC = timezone.utc
EXPORTER_ID = "p_mt5_utc_bundle_v1"
OFFICIAL_TIMEBASE_REFS = [
    "https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py",
    "https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py",
]


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "_asdict"):
        return {str(k): _json_safe(v) for k, v in value._asdict().items()}
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return str(value)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _file_record(path: Path, root: Path, rows: int, first_time: str | None, last_time: str | None, kind: str, timeframe: str | None = None) -> dict[str, Any]:
    record = {
        "path": path.relative_to(root).as_posix(),
        "kind": kind,
        "rows": rows,
        "first_time_utc": first_time,
        "last_time_utc": last_time,
        "sha256": sha256_file(path),
    }
    if timeframe:
        record["timeframe"] = timeframe
    return record


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only canonical UTC export from an already logged-in MetaTrader 5 terminal."
    )
    parser.add_argument("--symbol", required=True, help="Exact broker symbol, e.g. XAUUSD_o")
    parser.add_argument("--output", default="MT5_UTC_EXPORTS", help="Output root directory")
    parser.add_argument("--terminal", default=None, help="Optional full path to terminal64.exe")
    parser.add_argument("--bars-days", type=int, default=180, help="Calendar days for H1/M15/M5 bars")
    parser.add_argument("--ticks-days", type=int, default=2, help="Calendar days for ticks; 0 disables")
    args = parser.parse_args()

    if args.bars_days <= 0 or args.ticks_days < 0:
        parser.error("--bars-days must be > 0 and --ticks-days must be >= 0")

    try:
        import MetaTrader5 as mt5
    except ImportError:
        print("ERROR: MetaTrader5 package is required. Run: py -m pip install MetaTrader5")
        return 2

    initialized = mt5.initialize(args.terminal) if args.terminal else mt5.initialize()
    if not initialized:
        print(f"ERROR: mt5.initialize() failed: {mt5.last_error()}")
        return 2

    try:
        symbol_info = mt5.symbol_info(args.symbol)
        if symbol_info is None:
            print(f"ERROR: symbol not found: {args.symbol}")
            return 2
        if not symbol_info.visible and not mt5.symbol_select(args.symbol, True):
            print(f"ERROR: could not select symbol: {args.symbol}")
            return 2

        account = mt5.account_info()
        terminal = mt5.terminal_info()
        version = mt5.version()
        last_tick = mt5.symbol_info_tick(args.symbol)
        export_time = datetime.now(tz=UTC)
        cutoff_epoch = export_time.timestamp()
        start_bars = export_time - timedelta(days=args.bars_days)

        root = Path(args.output).expanduser().resolve()
        stamp = export_time.strftime("%Y%m%d_%H%M%S_UTC")
        bundle_dir = root / f"{args.symbol}_{stamp}"
        bundle_dir.mkdir(parents=True, exist_ok=False)

        tf_specs = [
            ("H1", mt5.TIMEFRAME_H1, 3600),
            ("M15", mt5.TIMEFRAME_M15, 900),
            ("M5", mt5.TIMEFRAME_M5, 300),
        ]

        file_records: list[dict[str, Any]] = []
        quality: dict[str, Any] = {"bars": {}, "ticks": None, "warnings": []}

        for label, tf_value, seconds in tf_specs:
            rates = mt5.copy_rates_range(args.symbol, tf_value, start_bars, export_time)
            if rates is None:
                raise RuntimeError(f"copy_rates_range failed for {label}: {mt5.last_error()}")

            rows: list[dict[str, Any]] = []
            for rate in rates:
                epoch = int(rate["time"])
                rows.append(
                    {
                        "time_utc": epoch_seconds_to_utc_iso(epoch),
                        "open": float(rate["open"]),
                        "high": float(rate["high"]),
                        "low": float(rate["low"]),
                        "close": float(rate["close"]),
                        "tick_volume": int(rate["tick_volume"]),
                        "spread": int(rate["spread"]),
                        "real_volume": int(rate["real_volume"]),
                        "is_closed": bar_is_closed(epoch, seconds, cutoff_epoch),
                        "time_epoch": epoch,
                    }
                )

            path = bundle_dir / f"{args.symbol}_{label}_bars_utc.csv"
            fields = [
                "time_utc",
                "open",
                "high",
                "low",
                "close",
                "tick_volume",
                "spread",
                "real_volume",
                "is_closed",
                "time_epoch",
            ]
            _write_csv(path, fields, rows)
            first_time = rows[0]["time_utc"] if rows else None
            last_time = rows[-1]["time_utc"] if rows else None
            file_records.append(_file_record(path, bundle_dir, len(rows), first_time, last_time, "ohlc", label))
            quality["bars"][label] = {
                "rows": len(rows),
                "first_time_utc": first_time,
                "last_time_utc": last_time,
                "forming_rows": sum(1 for row in rows if not row["is_closed"]),
            }

        if args.ticks_days > 0:
            tick_from = export_time - timedelta(days=args.ticks_days)
            ticks = mt5.copy_ticks_range(args.symbol, tick_from, export_time, mt5.COPY_TICKS_ALL)
            if ticks is None:
                raise RuntimeError(f"copy_ticks_range failed: {mt5.last_error()}")
            names = set(ticks.dtype.names or [])
            tick_rows: list[dict[str, Any]] = []
            for tick in ticks:
                time_msc = int(tick["time_msc"]) if "time_msc" in names else int(tick["time"]) * 1000
                tick_rows.append(
                    {
                        "time_utc": epoch_milliseconds_to_utc_iso(time_msc),
                        "time_msc": time_msc,
                        "bid": float(tick["bid"]) if "bid" in names else "",
                        "ask": float(tick["ask"]) if "ask" in names else "",
                        "last": float(tick["last"]) if "last" in names else "",
                        "volume": int(tick["volume"]) if "volume" in names else "",
                        "volume_real": float(tick["volume_real"]) if "volume_real" in names else "",
                        "flags": int(tick["flags"]) if "flags" in names else "",
                    }
                )
            tick_path = bundle_dir / f"{args.symbol}_ticks_utc.csv"
            tick_fields = ["time_utc", "time_msc", "bid", "ask", "last", "volume", "volume_real", "flags"]
            _write_csv(tick_path, tick_fields, tick_rows)
            first_tick = tick_rows[0]["time_utc"] if tick_rows else None
            last_tick_time = tick_rows[-1]["time_utc"] if tick_rows else None
            file_records.append(_file_record(tick_path, bundle_dir, len(tick_rows), first_tick, last_tick_time, "tick"))
            quality["ticks"] = {
                "rows": len(tick_rows),
                "first_time_utc": first_tick,
                "last_time_utc": last_tick_time,
            }

        manifest = {
            "schema_version": 1,
            "exporter": {
                "id": EXPORTER_ID,
                "version": "1.0.0",
                "read_only": True,
            },
            "timestamp_semantics": "utc_from_metatrader5_python_api",
            "official_timebase_references": OFFICIAL_TIMEBASE_REFS,
            "export_time_utc": export_time.isoformat(),
            "broker": {
                "company": getattr(account, "company", None) if account else None,
                "server": getattr(account, "server", None) if account else None,
            },
            "terminal": {
                "version": _json_safe(version),
                "connected": getattr(terminal, "connected", None) if terminal else None,
            },
            "symbol": {
                "name": args.symbol,
                "specification": _json_safe(symbol_info),
                "last_tick": _json_safe(last_tick),
            },
            "request": {
                "bars_days": args.bars_days,
                "ticks_days": args.ticks_days,
                "timeframes": ["H1", "M15", "M5"],
            },
            "files": file_records,
            "privacy": {
                "account_login_included": False,
                "password_included": False,
            },
            "binding_scope": "newly_generated_files_in_this_bundle_only",
            "legacy_source_local_bundle_retroactively_verified": False,
        }
        manifest_path = bundle_dir / "binding_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        quality_path = bundle_dir / "quality_report.json"
        quality_path.write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")

        zip_path = bundle_dir.with_suffix(".zip")
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for file in bundle_dir.rglob("*"):
                if file.is_file():
                    archive.write(file, file.relative_to(bundle_dir))

        print("SUCCESS")
        print(f"Bundle directory: {bundle_dir}")
        print(f"ZIP: {zip_path}")
        print(f"Broker/server: {manifest['broker']['company']} / {manifest['broker']['server']}")
        print("Timestamp semantics: UTC from MetaTrader5 Python API")
        print("No trading/order function is called by this exporter.")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    sys.exit(main())
