from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping

from .data_validation import extract_timestamp, read_csv_rows


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int | None = None


@dataclass(frozen=True)
class Tick:
    timestamp: datetime
    bid: float
    ask: float


def _key(value: str) -> str:
    return value.strip().lower().strip("<>").replace(" ", "_")


def _norm(row: Mapping[str, Any]) -> dict[str, Any]:
    return {_key(str(k)): v for k, v in row.items() if k is not None}


def _float(value: Any) -> float:
    return float(str(value).replace(",", "").strip())


def load_bars(path: str | Path) -> list[Bar]:
    rows, _ = read_csv_rows(path)
    result: list[Bar] = []
    for raw in rows:
        r = _norm(raw)
        result.append(
            Bar(
                timestamp=extract_timestamp(raw),
                open=_float(r["open"]),
                high=_float(r["high"]),
                low=_float(r["low"]),
                close=_float(r["close"]),
                tick_volume=int(float(r["tickvol"])) if str(r.get("tickvol", "")).strip() else None,
            )
        )
    return result


def load_ticks(path: str | Path) -> list[Tick]:
    rows, _ = read_csv_rows(path)
    result: list[Tick] = []
    for raw in rows:
        r = _norm(raw)
        result.append(
            Tick(
                timestamp=extract_timestamp(raw),
                bid=_float(r["bid"]),
                ask=_float(r["ask"]),
            )
        )
    return result


def floor_time(ts: datetime, minutes: int) -> datetime:
    if minutes <= 0 or 60 % minutes != 0:
        raise ValueError("minutes must be a positive divisor of 60")
    return ts.replace(minute=(ts.minute // minutes) * minutes, second=0, microsecond=0)


def _aggregate_bars(bars: Iterable[Bar], minutes: int) -> dict[datetime, dict[str, Any]]:
    groups: dict[datetime, dict[str, Any]] = {}
    for bar in bars:
        key = floor_time(bar.timestamp, minutes)
        g = groups.get(key)
        if g is None:
            groups[key] = {
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "count": 1,
                "tick_volume": bar.tick_volume if bar.tick_volume is not None else None,
            }
            continue
        g["high"] = max(g["high"], bar.high)
        g["low"] = min(g["low"], bar.low)
        g["close"] = bar.close
        g["count"] += 1
        if g["tick_volume"] is not None and bar.tick_volume is not None:
            g["tick_volume"] += bar.tick_volume
        else:
            g["tick_volume"] = None
    return groups


def _aggregate_ticks(ticks: Iterable[Tick], minutes: int) -> dict[datetime, dict[str, Any]]:
    groups: dict[datetime, dict[str, Any]] = {}
    for tick in ticks:
        key = floor_time(tick.timestamp, minutes)
        g = groups.get(key)
        if g is None:
            groups[key] = {
                "open": tick.bid,
                "high": tick.bid,
                "low": tick.bid,
                "close": tick.bid,
                "count": 1,
            }
            continue
        g["high"] = max(g["high"], tick.bid)
        g["low"] = min(g["low"], tick.bid)
        g["close"] = tick.bid
        g["count"] += 1
    return groups


def _compare_parent(
    child: list[Bar], parent: list[Bar], parent_minutes: int, expected_children: int
) -> dict[str, Any]:
    aggregated = _aggregate_bars(child, parent_minutes)
    parent_by_time = {b.timestamp: b for b in parent}
    comparable = 0
    ohlc_mismatches = 0
    tick_volume_mismatches = 0
    for ts, agg in aggregated.items():
        p = parent_by_time.get(ts)
        if p is None or agg["count"] != expected_children:
            continue
        comparable += 1
        if not (
            p.open == agg["open"]
            and p.high == agg["high"]
            and p.low == agg["low"]
            and p.close == agg["close"]
        ):
            ohlc_mismatches += 1
        if p.tick_volume is not None and agg["tick_volume"] is not None and p.tick_volume != agg["tick_volume"]:
            tick_volume_mismatches += 1
    return {
        "comparable_complete_groups": comparable,
        "ohlc_mismatches": ohlc_mismatches,
        "tick_volume_mismatches": tick_volume_mismatches,
    }


def _compare_ticks_to_bars(ticks: list[Tick], bars: list[Bar], minutes: int, cutoff: datetime) -> dict[str, Any]:
    aggregated = _aggregate_ticks(ticks, minutes)
    bars_by_time = {b.timestamp: b for b in bars}
    comparable = 0
    ohlc_mismatches = 0
    tick_count_mismatches: list[dict[str, Any]] = []
    delta = timedelta(minutes=minutes)

    for ts, agg in aggregated.items():
        if ts + delta > cutoff:
            continue
        bar = bars_by_time.get(ts)
        if bar is None:
            continue
        comparable += 1
        if not (
            bar.open == agg["open"]
            and bar.high == agg["high"]
            and bar.low == agg["low"]
            and bar.close == agg["close"]
        ):
            ohlc_mismatches += 1
        if bar.tick_volume is not None and bar.tick_volume != agg["count"]:
            tick_count_mismatches.append(
                {
                    "timestamp": ts.isoformat(),
                    "bar_tick_volume": bar.tick_volume,
                    "exported_tick_records": agg["count"],
                    "difference": bar.tick_volume - agg["count"],
                }
            )

    return {
        "comparable_completed_bars": comparable,
        "ohlc_mismatches": ohlc_mismatches,
        "tick_count_mismatches": tick_count_mismatches,
    }


def latest_closed_bar(bars: list[Bar], minutes: int, cutoff: datetime) -> datetime | None:
    delta = timedelta(minutes=minutes)
    closed = [bar.timestamp for bar in bars if bar.timestamp + delta <= cutoff]
    return max(closed) if closed else None


def qualify_bundle(
    *,
    h1_path: str | Path,
    m15_path: str | Path,
    m5_path: str | Path,
    tick_path: str | Path,
) -> dict[str, Any]:
    h1 = load_bars(h1_path)
    m15 = load_bars(m15_path)
    m5 = load_bars(m5_path)
    ticks = load_ticks(tick_path)
    if not ticks:
        raise ValueError("tick dataset is empty")

    cutoff = max(t.timestamp for t in ticks)
    first_tick = min(t.timestamp for t in ticks)

    return {
        "cutoff": cutoff.isoformat(),
        "first_tick": first_tick.isoformat(),
        "rows": {"H1": len(h1), "M15": len(m15), "M5": len(m5), "TICK": len(ticks)},
        "latest_closed_bar": {
            "H1": latest_closed_bar(h1, 60, cutoff).isoformat() if latest_closed_bar(h1, 60, cutoff) else None,
            "M15": latest_closed_bar(m15, 15, cutoff).isoformat() if latest_closed_bar(m15, 15, cutoff) else None,
            "M5": latest_closed_bar(m5, 5, cutoff).isoformat() if latest_closed_bar(m5, 5, cutoff) else None,
        },
        "cross_timeframe": {
            "M5_to_M15": _compare_parent(m5, m15, 15, 3),
            "M5_to_H1": _compare_parent(m5, h1, 60, 12),
            "M15_to_H1": _compare_parent(m15, h1, 60, 4),
        },
        "tick_reconstruction": {
            "M5": _compare_ticks_to_bars(ticks, m5, 5, cutoff),
            "M15": _compare_ticks_to_bars(ticks, m15, 15, cutoff),
            "H1": _compare_ticks_to_bars(ticks, h1, 60, cutoff),
        },
        "coverage_edges": {
            "H1_start": h1[0].timestamp.isoformat() if h1 else None,
            "M15_start": m15[0].timestamp.isoformat() if m15 else None,
            "M5_start": m5[0].timestamp.isoformat() if m5 else None,
        },
    }
