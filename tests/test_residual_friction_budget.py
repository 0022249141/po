from __future__ import annotations

import unittest

from research_core.residual_friction_budget import compute_residual_friction_budget


class ResidualFrictionBudgetTests(unittest.TestCase):
    def test_break_even_extra_price_is_exact_for_uniform_price_cost(self) -> None:
        ledger = [
            {"initial_risk": 1.0, "gross_R": 1.0},
            {"initial_risk": 2.0, "gross_R": -0.5},
        ]
        result = compute_residual_friction_budget(
            ledger,
            spread_price=0.2,
            spread_points=20.0,
            point_size=0.01,
        )
        self.assertAlmostEqual(result["base_metrics"]["expectancy"], 0.1)
        self.assertAlmostEqual(result["risk_geometry"]["sum_inverse_initial_risk"], 1.5)
        self.assertAlmostEqual(result["break_even_extra_round_trip_price"], 0.2 / 1.5)
        self.assertAlmostEqual(result["break_even_extra_round_trip_points"], (0.2 / 1.5) / 0.01)
        self.assertAlmostEqual(result["total_break_even_round_trip_points"], 20.0 + (0.2 / 1.5) / 0.01)

    def test_non_positive_risk_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            compute_residual_friction_budget(
                [{"initial_risk": 0.0, "gross_R": 1.0}],
                spread_price=0.2,
                spread_points=20.0,
                point_size=0.01,
            )


if __name__ == "__main__":
    unittest.main()
