import unittest
from datetime import datetime

from research_core.tpo_profile import TPOBar, TPOProfileEngine


class TPOProfileTests(unittest.TestCase):
    def test_closed_bar_populates_inclusive_bins(self):
        engine = TPOProfileEngine("0.01")
        contributed = engine.update(
            TPOBar(
                timestamp=datetime(2026, 1, 1, 10, 0),
                low="100.00",
                high="100.02",
                close_status="closed",
                session_id="s1",
            )
        )
        self.assertTrue(contributed)
        self.assertEqual(engine.snapshot()["bins"], {10000: 1, 10001: 1, 10002: 1})
        self.assertEqual(engine.snapshot()["bars_seen"], 1)

    def test_forming_bar_is_strict_noop_then_same_bar_can_close(self):
        engine = TPOProfileEngine("0.01")
        ts = datetime(2026, 1, 1, 10, 0)
        self.assertFalse(
            engine.update(
                TPOBar(ts, "100.00", "100.01", "forming", "s1")
            )
        )
        self.assertEqual(engine.snapshot()["bins"], {})
        self.assertTrue(
            engine.update(
                TPOBar(ts, "100.00", "100.01", "closed", "s1")
            )
        )
        self.assertEqual(engine.snapshot()["bins"], {10000: 1, 10001: 1})

    def test_session_change_resets_current_profile(self):
        engine = TPOProfileEngine("0.01")
        engine.update(TPOBar(datetime(2026, 1, 1, 10, 0), "100.00", "100.01", "closed", "s1"))
        engine.update(TPOBar(datetime(2026, 1, 1, 10, 5), "101.00", "101.00", "closed", "s2"))
        snapshot = engine.snapshot()
        self.assertEqual(snapshot["session_id"], "s2")
        self.assertEqual(snapshot["bins"], {10100: 1})
        self.assertEqual(snapshot["bars_seen"], 1)

    def test_closed_bar_ordering_is_strict(self):
        engine = TPOProfileEngine("0.01")
        ts = datetime(2026, 1, 1, 10, 0)
        engine.update(TPOBar(ts, "100.00", "100.00", "closed", "s1"))
        with self.assertRaises(ValueError):
            engine.update(TPOBar(ts, "100.00", "100.00", "closed", "s1"))

    def test_gap_flag_marks_profile_incomplete(self):
        engine = TPOProfileEngine("0.01")
        engine.update(
            TPOBar(
                timestamp=datetime(2026, 1, 1, 10, 0),
                low="100.00",
                high="100.00",
                close_status="closed",
                session_id="s1",
                gap_before=True,
            )
        )
        snapshot = engine.snapshot()
        self.assertTrue(snapshot["incomplete"])
        self.assertIn("source_gap_before_bar", snapshot["incomplete_reasons"])


if __name__ == "__main__":
    unittest.main()
