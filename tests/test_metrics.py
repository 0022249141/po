import unittest

from research_core.metrics import summarize_pnls, summarize_trades


class MetricsTests(unittest.TestCase):
    def test_summary(self):
        result = summarize_pnls([10, -5, 20, -10], initial_capital=100)
        self.assertEqual(result["trades"], 4)
        self.assertEqual(result["net_profit"], 15)
        self.assertAlmostEqual(result["profit_factor"], 2.0)
        self.assertAlmostEqual(result["expectancy"], 3.75)
        self.assertEqual(result["max_consecutive_losses"], 1)

    def test_side_split(self):
        result = summarize_trades([
            {"pnl": 5, "side": "buy"},
            {"pnl": -2, "side": "sell"},
        ])
        self.assertIn("long", result["by_side"])
        self.assertIn("short", result["by_side"])


if __name__ == "__main__":
    unittest.main()
