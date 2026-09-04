from __future__ import annotations

import csv
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, Mapping, Any


TIMEFRAME_SECONDS = {
    "M1": 60,
    "M2": 120,
    "M3": 180,
    "M4": 240,
    "M5": 300,
    "M6": 360,
    "M10": 600,
    "M12": 720,
    "M15": 900,
    "M20": 1200,
    "M30": 1800,
    "H1": 3600,
    "H2": 7200,
    "H3": 10800,
    "H4": 14400,
    "H6": 21600,
    "H8": 28800,
    "H12": 43200,
    "D1": 86400,
}


@dataclass
class Issue:
    severity: str
    code: str
    message: str
    row: int | None = None


def _key(value: str) -> str:
    return value.strip().lower().strip("<>").replace(" ", "_")


def _norm_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {_key(str(k)): v for k, v in row.items() if k is not None}


def _float(value: Any) -> float:
    if value is None or str(value).strip() == "":
        raise ValueError("empty numeric value")
    return float(str(value).replace(",", "").strip())


def parse_timestamp(value: str) -> datetime:
    text = str(value).strip()
    if not text:
        raise ValueError("empty timestamp")

    # ISO 8601 first. Convert Z for Python compatibility.
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        pass

    formats = (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y.%m.%d %H:%M:%S.%f",
        "%Y.%m.%d %H:%M:%S",
        "%Y.%m.%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%d.%m.%Y %H:%M:%S",
        "%d.%m.%Y %H:%M",
    )
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"unsupported timestamp format: {text!r}")


def extract_timestamp(row: Mapping[str, Any]) -> datetime:
    r = _norm_row(row)
    date = r.get("date")
    time_only = r.get("time")
    if date not in (None, "") and time_only not in (None, ""):
        return parse_timestamp(f"{date} {time_only}")

    for name in ("timestamp", "datetime", "date_time", "time", "date"):
        if name in r and str(r[name]).strip():
            return parse_timestamp(str(r[name]))
    raise ValueError("no timestamp/date-time column found")


def _issue(target: list[Issue], severity: str, code: str, message: str, row: int | None = None) -> None:
    # Keep report size bounded while counts can still be derived from the retained list for normal files.
    if len(target) < 500:
        target.append(Issue(severity, code, message, row))


def _find(r: Mapping[str, Any], *names: str) -> Any:
    for name in names:
        if name in r:
            return r[name]
    raise KeyError(names[0])


def validate_ohlc_rows(rows: Iterable[Mapping[str, Any]], timeframe: str | None = None) -> dict[str, Any]:
    issues: list[Issue] = []
    count = 0
    previous_ts: datetime | None = None
    min_ts: datetime | None = None
    max_ts: datetime | None = None
    duplicate_count = 0
    gap_count = 0
    expected = TIMEFRAME_SECONDS.get(timeframe.upper()) if timeframe else None

    for row_number, raw in enumerate(rows, start=2):
        count += 1
        r = _norm_row(raw)
        try:
            ts = extract_timestamp(r)
        except Exception as exc:
            _issue(issues, "error", "timestamp_invalid", str(exc), row_number)
            continue

        if min_ts is None or ts < min_ts:
            min_ts = ts
        if max_ts is None or ts > max_ts:
            max_ts = ts

        if previous_ts is not None:
            if ts < previous_ts:
                _issue(issues, "error", "timestamp_out_of_order", f"{ts} < {previous_ts}", row_number)
            elif ts == previous_ts:
                duplicate_count += 1
                _issue(issues, "error", "duplicate_timestamp", str(ts), row_number)
            elif expected is not None:
                delta = (ts - previous_ts).total_seconds()
                if delta > expected * 1.5:
                    gap_count += 1
                    _issue(
                        issues,
                        "warning",
                        "interval_gap",
                        f"gap {delta:.0f}s exceeds expected {expected}s; review session/calendar",
                        row_number,
                    )
        previous_ts = ts

        try:
            o = _float(_find(r, "open"))
            h = _float(_find(r, "high"))
            l = _float(_find(r, "low"))
            c = _float(_find(r, "close"))
        except Exception as exc:
            _issue(issues, "error", "ohlc_invalid", str(exc), row_number)
            continue

        if h < max(o, l, c):
            _issue(issues, "error", "high_inconsistent", f"high={h} < max(open,low,close)", row_number)
        if l > min(o, h, c):
            _issue(issues, "error", "low_inconsistent", f"low={l} > min(open,high,close)", row_number)

        for volume_name in ("volume", "tick_volume", "vol"):
            if volume_name in r and str(r[volume_name]).strip():
                try:
                    if _float(r[volume_name]) < 0:
                        _issue(issues, "error", "negative_volume", volume_name, row_number)
                except ValueError:
                    _issue(issues, "warning", "volume_non_numeric", volume_name, row_number)

    if count == 0:
        _issue(issues, "error", "empty_dataset", "no data rows")

    errors = sum(i.severity == "error" for i in issues)
    warnings = sum(i.severity == "warning" for i in issues)
    status = "fail" if errors else ("pass_with_warnings" if warnings else "pass")
    return {
        "data_type": "ohlc",
        "status": status,
        "rows": count,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "start_timestamp": min_ts.isoformat() if min_ts else None,
            "end_timestamp": max_ts.isoformat() if max_ts else None,
            "duplicate_timestamps": duplicate_count,
            "reported_gaps": gap_count,
            "timeframe": timeframe,
        },
        "issues": [asdict(i) for i in issues],
    }


def validate_tick_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    issues: list[Issue] = []
    count = 0
    previous_ts: datetime | None = None
    min_ts: datetime | None = None
    max_ts: datetime | None = None
    duplicate_count = 0
    spreads: list[float] = []

    for row_number, raw in enumerate(rows, start=2):
        count += 1
        r = _norm_row(raw)
        try:
            ts = extract_timestamp(r)
        except Exception as exc:
            _issue(issues, "error", "timestamp_invalid", str(exc), row_number)
            continue

        if min_ts is None or ts < min_ts:
            min_ts = ts
        if max_ts is None or ts > max_ts:
            max_ts = ts
        if previous_ts is not None:
            if ts < previous_ts:
                _issue(issues, "error", "timestamp_out_of_order", f"{ts} < {previous_ts}", row_number)
            elif ts == previous_ts:
                duplicate_count += 1
                _issue(issues, "warning", "duplicate_timestamp", "may be legitimate if source precision is coarse", row_number)
        previous_ts = ts

        try:
            bid = _float(_find(r, "bid"))
            ask = _float(_find(r, "ask"))
        except Exception as exc:
            _issue(issues, "error", "quote_invalid", str(exc), row_number)
            continue

        if bid > ask:
            _issue(issues, "error", "crossed_quote", f"bid={bid} > ask={ask}", row_number)
        else:
            spreads.append(ask - bid)

    if count == 0:
        _issue(issues, "error", "empty_dataset", "no data rows")

    errors = sum(i.severity == "error" for i in issues)
    warnings = sum(i.severity == "warning" for i in issues)
    status = "fail" if errors else ("pass_with_warnings" if warnings else "pass")
    return {
        "data_type": "tick",
        "status": status,
        "rows": count,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "start_timestamp": min_ts.isoformat() if min_ts else None,
            "end_timestamp": max_ts.isoformat() if max_ts else None,
            "duplicate_timestamps": duplicate_count,
            "min_spread": min(spreads) if spreads else None,
            "max_spread": max(spreads) if spreads else None,
            "avg_spread": (sum(spreads) / len(spreads)) if spreads else None,
        },
        "issues": [asdict(i) for i in issues],
    }


def read_csv_rows(path: str | Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    path = Path(path)
    last_exc: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            text = path.read_text(encoding=encoding)
            sample = text[:8192]
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                delimiter = dialect.delimiter
            except csv.Error:
                delimiter = ","
            reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
            rows = list(reader)
            return rows, {"encoding": encoding, "delimiter": delimiter, "headers": reader.fieldnames or []}
        except UnicodeDecodeError as exc:
            last_exc = exc
    raise ValueError(f"unable to decode CSV: {last_exc}")


def validate_market_csv(path: str | Path, data_type: str, timeframe: str | None = None) -> dict[str, Any]:
    rows, csv_meta = read_csv_rows(path)
    if data_type == "ohlc":
        result = validate_ohlc_rows(rows, timeframe=timeframe)
    elif data_type == "tick":
        result = validate_tick_rows(rows)
    else:
        raise ValueError("data_type must be 'ohlc' or 'tick'")
    result["file"] = str(Path(path))
    result["csv"] = csv_meta
    return result
