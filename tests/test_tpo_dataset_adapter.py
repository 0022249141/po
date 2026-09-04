import tempfile
import unittest
from pathlib import Path

from research_core.tpo_dataset_adapter import build_source_day_tpo


HEADER = "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\n"


class TPODatasetAdapterTests(unittest.TestCase):
    def _write(self, rows: list[str]) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
        tmp.write(HEADER + "".join(rows))
        tmp.close()
        self.addCleanup(lambda: Path(tmp.name).unlink(missing_ok=True))
        return Path(tmp.name)

    def test_cutoff_excludes_forming_bar_from_profile(self):
        path = self._write([
            "2026.09.03\t09:10:00\t100.0\t100.2\t100.0\t100.1\t1\t0\t10\n",
            "2026.09.03\t09:15:00\t100.1\t100.3\t100.1\t100.2\t1\t0\t10\n",
            "2026.09.03\t09:20:00\t100.2\t101.0\t99.0\t100.4\t1\t0\t10\n",
        ])
        result = build_source_day_tpo(
            path,
            timeframe="M5",
            cutoff="2026-09-03T09:22:00",
            price_increment="0.1",
        )
        self.assertEqual(result["counts"]["closed_rows"], 2)
        self.assertEqual(result["counts"]["forming_rows"], 1)
        self.assertEqual(result["current_source_day_profile"]["bars_seen"], 2)
        self.assertEqual(result["current_source_day_profile"]["observed_session_high_tick"], 1003)

    def test_source_day_is_neutral_not_named_market_session(self):
        path = self._write([
            "2026.09.03\t09:00:00\t100.0\t100.0\t100.0\t100.0\t1\t0\t10\n",
        ])
        result = build_source_day_tpo(
            path,
            timeframe="M5",
            cutoff="2026-09-03T09:05:00",
            price_increment="0.1",
        )
        self.assertEqual(result["current_source_day_profile"]["session_id"], "source-day:2026-09-03")
        self.assertEqual(result["policy"]["timestamp_semantics"], "source_local_unknown_timezone")
        self.assertTrue(result["interpretation_boundary"]["not_london_newyork_asia_session"])

    def test_intra_day_gap_marks_profile_incomplete(self):
        path = self._write([
            "2026.09.03\t09:00:00\t100.0\t100.1\t100.0\t100.1\t1\t0\t10\n",
            "2026.09.03\t09:10:00\t100.1\t100.2\t100.1\t100.2\t1\t0\t10\n",
        ])
        result = build_source_day_tpo(
            path,
            timeframe="M5",
            cutoff="2026-09-03T09:15:00",
            price_increment="0.1",
        )
        self.assertTrue(result["current_source_day_profile"]["incomplete"])
        self.assertIn("source_gap_before_bar", result["current_source_day_profile"]["incomplete_reasons"])

    def test_cross_day_gap_does_not_contaminate_new_source_day(self):
        path = self._write([
            "2026.09.02\t23:55:00\t100.0\t100.1\t100.0\t100.1\t1\t0\t10\n",
            "2026.09.03\t01:00:00\t101.0\t101.1\t101.0\t101.1\t1\t0\t10\n",
        ])
        result = build_source_day_tpo(
            path,
            timeframe="M5",
            cutoff="2026-09-03T01:05:00",
            price_increment="0.1",
        )
        self.assertFalse(result["current_source_day_profile"]["incomplete"])
        self.assertEqual(result["current_source_day_profile"]["bars_seen"], 1)


if __name__ == "__main__":
    unittest.main()
