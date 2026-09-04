from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from research_core.spread_sensitivity import run_spread_sensitivity


class SpreadSensitivityTests(unittest.TestCase):
    def test_fixed_spread_deduction_is_applied_in_R(self):
        gross = {
            "backtest_class": "gross_signal_research_v1",
            "strategy_spec_id": "xauusd_ny_preopen_range_breakout_baseline_v1",
            "trade_ledger": [
                {
                    "session_date": "2026-06-01",
                    "side": "long",
                    "entry_ts_utc": "2026-06-01T12:00:00+00:00",
                    "initial_risk": 10.0,
                    "gross_R": 1.0,
                },
                {
                    "session_date": "2026-06-02",
                    "side": "short",
                    "entry_ts_utc": "2026-06-02T12:00:00+00:00",
                    "initial_risk": 20.0,
                    "gross_R": -0.5,
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "gross.json"
            path.write_text(json.dumps(gross), encoding="utf-8")
            result = run_spread_sensitivity(path, repo_root=".", include_adjusted_ledger=True)
        median = result["scenario_results"]["observed_median_fixed"]
        rows = median["adjusted_ledger"]
        self.assertAlmostEqual(rows[0]["spread_cost_R"], 0.022)
        self.assertAlmostEqual(rows[0]["adjusted_R"], 0.978)
        self.assertAlmostEqual(rows[1]["spread_cost_R"], 0.011)
        self.assertAlmostEqual(rows[1]["adjusted_R"], -0.511)


if __name__ == "__main__":
    unittest.main()
