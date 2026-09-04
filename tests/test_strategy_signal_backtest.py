from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from research_core.strategy_signal_backtest import run_strategy_signal_backtest


UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[1]


def _write_case(path: Path, *, mode: str, missing_ref_ts: datetime | None = None) -> None:
    start = datetime(2026, 7, 15, 8, 0, tzinfo=UTC)
    end = datetime(2026, 7, 15, 21, 0, tzinfo=UTC)
    current = start
    rows: list[dict[str, object]] = []
    while current < end:
        if current == missing_ref_ts:
            current += timedelta(minutes=5)
            continue

        if current < datetime(2026, 7, 15, 12, 0, tzinfo=UTC):
            if mode == "short_stop":
                o, h, l, c = 105.0, 110.0, 100.0, 105.0
            else:
                o, h, l, c = 95.0, 100.0, 90.0, 95.0
        else:
            if mode in {"long_time_exit", "long_gap_stop"}:
                o, h, l, c = 95.0, 99.0, 91.0, 95.0
                if current == datetime(2026, 7, 15, 12, 10, tzinfo=UTC):
                    o, h, l, c = 96.0, 102.0, 95.0, 101.0
                elif current == datetime(2026, 7, 15, 12, 15, tzinfo=UTC):
                    o, h, l, c = 102.0, 103.0, 100.0, 102.0
                elif mode == "long_gap_stop" and current == datetime(2026, 7, 15, 12, 20, tzinfo=UTC):
                    o, h, l, c = 85.0, 88.0, 84.0, 86.0
                elif current > datetime(2026, 7, 15, 12, 15, tzinfo=UTC):
                    o, h, l, c = 106.0, 109.0, 100.0, 108.0
            elif mode == "short_stop":
                o, h, l, c = 105.0, 109.0, 101.0, 105.0
                if current == datetime(2026, 7, 15, 12, 10, tzinfo=UTC):
                    o, h, l, c = 104.0, 105.0, 98.0, 99.0
                elif current == datetime(2026, 7, 15, 12, 15, tzinfo=UTC):
                    o, h, l, c = 98.0, 111.0, 97.0, 100.0
            else:
                raise ValueError(mode)

        rows.append({"time_utc": current.isoformat().replace("+00:00", "Z"), "open": o, "high": h, "low": l, "close": c})
        current += timedelta(minutes=5)

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["time_utc", "open", "high", "low", "close"])
        writer.writeheader()
        writer.writerows(rows)


class StrategySignalBacktestTests(unittest.TestCase):
    def _run(self, mode: str, missing_ref_ts: datetime | None = None):
        with TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "case.csv"
            _write_case(csv_path, mode=mode, missing_ref_ts=missing_ref_ts)
            return run_strategy_signal_backtest(csv_path, repo_root=ROOT, include_regime_reporting=False)

    def test_long_uses_next_bar_open_and_time_exit(self) -> None:
        result = self._run("long_time_exit")
        self.assertEqual(result["trade_count"], 1)
        trade = result["trade_ledger"][0]
        self.assertEqual(trade["side"], "long")
        self.assertEqual(trade["entry_ts_utc"], "2026-07-15T12:15:00+00:00")
        self.assertEqual(trade["entry_price"], 102.0)
        self.assertEqual(trade["exit_reason"], "session_time_exit")
        self.assertAlmostEqual(trade["gross_R"], 0.5)

    def test_stop_is_active_on_entry_bar(self) -> None:
        result = self._run("short_stop")
        trade = result["trade_ledger"][0]
        self.assertEqual(trade["side"], "short")
        self.assertEqual(trade["exit_reason"], "protective_stop")
        self.assertAlmostEqual(trade["gross_R"], -1.0)

    def test_gap_through_stop_can_be_worse_than_minus_one_R(self) -> None:
        result = self._run("long_gap_stop")
        trade = result["trade_ledger"][0]
        self.assertEqual(trade["exit_reason"], "protective_stop_gap")
        self.assertLess(trade["gross_R"], -1.0)

    def test_missing_reference_bar_excludes_session(self) -> None:
        result = self._run("long_time_exit", datetime(2026, 7, 15, 10, 0, tzinfo=UTC))
        self.assertEqual(result["trade_count"], 0)
        self.assertGreaterEqual(result["skipped_session_or_signal_counts"].get("incomplete_reference_range", 0), 1)


if __name__ == "__main__":
    unittest.main()
