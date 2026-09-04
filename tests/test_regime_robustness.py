from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path
import unittest

import yaml

from research_core.regime_robustness import assign_lagged_range_regimes
from research_core.regime_robustness_validation import validate_regime_robustness_spec


ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "quant" / "studies" / "XAUUSD_NAMED_SESSION_TPO_REGIME_ROBUSTNESS_V1.yaml"


def _row(session: str, day: date, range_ticks: float) -> dict[str, float | str]:
    occupied = range_ticks + 1.0
    occupancy_events = range_ticks * 10.0
    return {
        "session_id": session,
        "session_instance_id": f"{session}:{day.isoformat()}",
        "range_ticks": float(range_ticks),
        "occupied_bins": float(occupied),
        "occupancy_events": float(occupancy_events),
        "mean_bin_occupancy": float(occupancy_events / occupied),
        "bars_seen": 108.0,
    }


class RegimeRobustnessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))

    def test_repository_regime_robustness_spec(self) -> None:
        result = validate_regime_robustness_spec(SPEC_PATH, ROOT)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])

    def test_current_date_outcome_cannot_change_its_own_label(self) -> None:
        start = date(2026, 1, 1)
        rows = {"london": [], "new_york": []}
        for offset in range(21):
            day = start + timedelta(days=offset)
            base = float(offset + 1)
            rows["london"].append(_row("london", day, base))
            rows["new_york"].append(_row("new_york", day, base + 2.0))

        original = assign_lagged_range_regimes(rows, self.spec)
        mutated_rows = deepcopy(rows)
        mutated_rows["london"][-1]["range_ticks"] = 999999.0
        mutated_rows["new_york"][-1]["range_ticks"] = 999999.0
        mutated = assign_lagged_range_regimes(mutated_rows, self.spec)

        self.assertEqual(len(original["date_assignments"]), 1)
        self.assertEqual(original["date_assignments"][0]["regime"], "high")
        self.assertEqual(
            original["date_assignments"][0]["regime"],
            mutated["date_assignments"][0]["regime"],
        )
        self.assertEqual(
            original["date_assignments"][0]["midrank_percentile"],
            mutated["date_assignments"][0]["midrank_percentile"],
        )

    def test_decreasing_prior_window_classifies_low(self) -> None:
        start = date(2026, 1, 1)
        rows = {"london": [], "new_york": []}
        for offset in range(21):
            day = start + timedelta(days=offset)
            base = float(100 - offset)
            rows["london"].append(_row("london", day, base))
            rows["new_york"].append(_row("new_york", day, base + 2.0))

        result = assign_lagged_range_regimes(rows, self.spec)
        self.assertEqual(result["date_assignments"][0]["regime"], "low")


if __name__ == "__main__":
    unittest.main()
