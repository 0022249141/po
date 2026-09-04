from __future__ import annotations

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from research_core.tpo_study import run_named_session_tpo_study


class TPOStudyTests(unittest.TestCase):
    def test_complete_sessions_are_summarized_without_significance_claim(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "synthetic_utc.csv"
            start = datetime(2026, 7, 6, 0, 0, tzinfo=timezone.utc)  # Monday
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=["timestamp", "open", "high", "low", "close"])
                writer.writeheader()
                for index in range(21 * 12):  # 00:00 through 20:55 UTC
                    ts = start + timedelta(minutes=5 * index)
                    writer.writerow(
                        {
                            "timestamp": ts.isoformat().replace("+00:00", "Z"),
                            "open": "100.05",
                            "high": "100.10",
                            "low": "100.00",
                            "close": "100.05",
                        }
                    )

            result = run_named_session_tpo_study(
                path,
                spec_path="quant/studies/XAUUSD_NAMED_SESSION_TPO_DESCRIPTIVE_V1.yaml",
                repo_root=root,
            )

            self.assertEqual("xauusd_named_session_tpo_descriptive_v1", result["study_id"])
            self.assertEqual("none", result["primary_comparison"]["statistical_significance_test"])
            self.assertEqual("underpowered", result["primary_comparison"]["status"])
            for session_id in ("asia_tokyo", "london", "new_york"):
                summary = result["session_summaries"][session_id]
                self.assertEqual(1, summary["n"])
                self.assertEqual(108.0, summary["features"]["bars_seen"]["median"])
                self.assertEqual(10.0, summary["features"]["range_ticks"]["median"])
                self.assertEqual(11.0, summary["features"]["occupied_bins"]["median"])


if __name__ == "__main__":
    unittest.main()
