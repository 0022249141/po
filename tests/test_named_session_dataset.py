from __future__ import annotations

import csv
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research_core.named_session_dataset import (
    ALLOW_INCOMPLETE_WITH_FLAG,
    SessionSelectionPolicy,
    build_named_session_tpo,
)
from research_core.session_policy import NamedSessionPolicy


UTC = timezone.utc
POLICY_PATH = Path("config/session-policies/xauusd-major-sessions.yaml")


class NamedSessionDatasetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = NamedSessionPolicy.from_yaml(POLICY_PATH)

    def _write_m5(self, opens: list[datetime], *, utc_header: bool = True) -> Path:
        handle = tempfile.NamedTemporaryFile("w", newline="", suffix=".csv", delete=False, encoding="utf-8")
        path = Path(handle.name)
        field = "time_utc" if utc_header else "timestamp"
        writer = csv.DictWriter(handle, fieldnames=[field, "open", "high", "low", "close"])
        writer.writeheader()
        for index, ts in enumerate(opens):
            base = 4400 + index * 0.01
            value = ts.isoformat().replace("+00:00", "Z") if utc_header else ts.replace(tzinfo=None).isoformat()
            writer.writerow(
                {
                    field: value,
                    "open": f"{base:.2f}",
                    "high": f"{base + 0.10:.2f}",
                    "low": f"{base - 0.10:.2f}",
                    "close": f"{base + 0.02:.2f}",
                }
            )
        handle.close()
        self.addCleanup(path.unlink, missing_ok=True)
        return path

    @staticmethod
    def _london_summer_opens() -> list[datetime]:
        # 2026-07-01 London 08:00-17:00 local = 07:00-16:00 UTC.
        start = datetime(2026, 7, 1, 7, 0, tzinfo=UTC)
        return [start + timedelta(minutes=5 * i) for i in range(108)]

    def test_complete_only_accepts_full_canonical_session(self) -> None:
        path = self._write_m5(self._london_summer_opens())
        result = build_named_session_tpo(
            path,
            timeframe="M5",
            cutoff="2026-07-01T16:00:00Z",
            price_increment="0.01",
            session_policy=self.policy,
            session_ids=["london"],
        )
        self.assertEqual(result["counts"]["selected_instances"], 1)
        item = result["instances"][0]
        self.assertTrue(item["complete"])
        self.assertEqual(item["expected_bars"], 108)
        self.assertEqual(item["observed_bars"], 108)
        self.assertEqual(item["profile"]["bars_seen"], 108)
        self.assertFalse(item["profile"]["incomplete"])

    def test_complete_only_excludes_missing_bar_instance(self) -> None:
        opens = self._london_summer_opens()
        path = self._write_m5(opens[:36] + opens[37:])
        result = build_named_session_tpo(
            path,
            timeframe="M5",
            cutoff="2026-07-01T16:00:00Z",
            price_increment="0.01",
            session_policy=self.policy,
            session_ids=["london"],
        )
        self.assertEqual(result["counts"]["selected_instances"], 0)
        self.assertEqual(result["counts"]["excluded_incomplete"], 1)

    def test_allow_incomplete_retains_flag_and_missing_open(self) -> None:
        opens = self._london_summer_opens()
        missing = opens[36]
        path = self._write_m5(opens[:36] + opens[37:])
        result = build_named_session_tpo(
            path,
            timeframe="M5",
            cutoff="2026-07-01T16:00:00Z",
            price_increment="0.01",
            session_policy=self.policy,
            session_ids=["london"],
            selection_policy=SessionSelectionPolicy(
                completeness_mode=ALLOW_INCOMPLETE_WITH_FLAG,
                exclude_coverage_edges=True,
            ),
        )
        item = result["instances"][0]
        self.assertFalse(item["complete"])
        self.assertEqual(item["missing_bars"], 1)
        self.assertEqual(item["missing_open_utc"], [missing.isoformat()])
        self.assertTrue(item["profile"]["incomplete"])
        self.assertIn("session_missing_expected_bars", item["profile"]["incomplete_reasons"])

    def test_coverage_edge_is_excluded_by_default(self) -> None:
        opens = self._london_summer_opens()[1:]
        path = self._write_m5(opens)
        result = build_named_session_tpo(
            path,
            timeframe="M5",
            cutoff="2026-07-01T16:00:00Z",
            price_increment="0.01",
            session_policy=self.policy,
            session_ids=["london"],
        )
        self.assertEqual(result["counts"]["selected_instances"], 0)
        self.assertEqual(result["counts"]["excluded_coverage_edge"], 1)

    def test_naive_timestamp_input_is_rejected(self) -> None:
        path = self._write_m5(self._london_summer_opens(), utc_header=False)
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            build_named_session_tpo(
                path,
                timeframe="M5",
                cutoff="2026-07-01T16:00:00Z",
                price_increment="0.01",
                session_policy=self.policy,
                session_ids=["london"],
            )


if __name__ == "__main__":
    unittest.main()
