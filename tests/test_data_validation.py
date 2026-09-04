import unittest

from research_core.data_validation import validate_ohlc_rows, validate_tick_rows


class DataValidationTests(unittest.TestCase):
    def test_valid_ohlc(self):
        rows = [
            {"timestamp": "2026-01-01 00:00:00", "open": "10", "high": "12", "low": "9", "close": "11"},
            {"timestamp": "2026-01-01 00:05:00", "open": "11", "high": "13", "low": "10", "close": "12"},
        ]
        report = validate_ohlc_rows(rows, timeframe="M5")
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["rows"], 2)

    def test_inconsistent_ohlc_fails(self):
        rows = [{"timestamp": "2026-01-01 00:00:00", "open": "10", "high": "9", "low": "8", "close": "11"}]
        report = validate_ohlc_rows(rows)
        self.assertEqual(report["status"], "fail")

    def test_crossed_tick_fails(self):
        rows = [{"timestamp": "2026-01-01 00:00:00", "bid": "101", "ask": "100"}]
        report = validate_tick_rows(rows)
        self.assertEqual(report["status"], "fail")


if __name__ == "__main__":
    unittest.main()
