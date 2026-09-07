from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import unittest

from research_core.range_compression_study import (
    annotate_reference_width_history,
    annotate_trade_ledger,
    breakout_penetration,
    build_descriptive_breakdowns,
    compression_bucket,
    midrank_percentile,
    run_range_compression_study,
    summarize_descriptive_cell,
)


ROOT = Path(__file__).resolve().parents[1]


def _reference_rows(widths: list[float]) -> list[dict[str, float | str]]:
    start = date(2026, 1, 1)
    return [
        {
            "session_date": (start + timedelta(days=index * 2)).isoformat(),
            "reference_high": 100.0 + width,
            "reference_low": 100.0,
            "current_reference_width": width,
        }
        for index, width in enumerate(widths)
    ]


class RangeCompressionStudyTests(unittest.TestCase):
    def test_current_width_does_not_change_its_own_lagged_baseline(self) -> None:
        widths = [float(index) for index in range(1, 21)] + [10.5]
        original = annotate_reference_width_history(_reference_rows(widths))[-1]
        mutated = annotate_reference_width_history(_reference_rows(widths[:-1] + [100.0]))[-1]

        self.assertEqual(original["lagged_20_reference_width_median"], 10.5)
        self.assertEqual(mutated["lagged_20_reference_width_median"], 10.5)
        self.assertNotEqual(original["relative_range_ratio"], mutated["relative_range_ratio"])
        self.assertNotEqual(
            original["reference_width_midrank_percentile"],
            mutated["reference_width_midrank_percentile"],
        )

    def test_prior_eligible_history_ignores_calendar_gaps(self) -> None:
        rows = _reference_rows([float(index) for index in range(1, 22)])
        result = annotate_reference_width_history(rows)
        self.assertEqual(result[-1]["lagged_20_reference_width_median"], 10.5)
        self.assertEqual(result[-1]["eligible_reference_width_index"], 20)
        self.assertEqual(result[-1]["compression_bucket"], "expanded")

    def test_reference_width_must_match_reference_high_minus_low(self) -> None:
        rows = _reference_rows([float(index) for index in range(1, 22)])
        rows[0]["current_reference_width"] = 999.0
        with self.assertRaisesRegex(ValueError, "current_reference_width must equal reference_high - reference_low"):
            annotate_reference_width_history(rows)

    def test_midrank_ties_and_frozen_thirds(self) -> None:
        self.assertAlmostEqual(0.5, midrank_percentile(2.0, [1.0, 2.0, 2.0, 3.0]))
        self.assertEqual("compressed", compression_bucket(0.0))
        self.assertEqual("normal", compression_bucket(1.0 / 3.0))
        self.assertEqual("expanded", compression_bucket(2.0 / 3.0))
        self.assertEqual("expanded", compression_bucket(1.0))

    def test_breakout_penetration_is_side_specific_and_can_be_negative(self) -> None:
        self.assertEqual(
            5.0,
            breakout_penetration({"side": "long", "entry_price": 105.0, "reference_high": 100.0, "reference_low": 90.0}),
        )
        self.assertEqual(
            5.0,
            breakout_penetration({"side": "short", "entry_price": 85.0, "reference_high": 100.0, "reference_low": 90.0}),
        )
        self.assertEqual(
            -1.0,
            breakout_penetration({"side": "long", "entry_price": 99.0, "reference_high": 100.0, "reference_low": 90.0}),
        )

    def test_all_source_trades_are_retained_while_warmup_is_explicit(self) -> None:
        history = annotate_reference_width_history(_reference_rows([float(index) for index in range(1, 22)]))
        warmup = history[0]
        assigned = history[-1]
        ledger = [
            {
                "session_date": warmup["session_date"],
                "side": "long",
                "entry_price": float(warmup["reference_high"]) + 1.0,
                "reference_high": warmup["reference_high"],
                "reference_low": warmup["reference_low"],
                "exit_reason": "session_time_exit",
                "gross_R": 0.25,
                "regime": None,
            },
            {
                "session_date": assigned["session_date"],
                "side": "short",
                "entry_price": float(assigned["reference_low"]) - 1.0,
                "reference_high": assigned["reference_high"],
                "reference_low": assigned["reference_low"],
                "exit_reason": "protective_stop",
                "gross_R": -1.0,
                "regime": "high",
            },
        ]
        annotated = annotate_trade_ledger(ledger, history)
        breakdowns = build_descriptive_breakdowns(annotated)

        self.assertEqual(2, len(annotated))
        self.assertIsNone(annotated[0]["compression_bucket"])
        self.assertEqual("assigned_causal_prior_only", annotated[1]["causal_feature_status"])
        self.assertEqual(2, breakdowns["overall"]["trades"])
        self.assertEqual(1, breakdowns["by_compression_bucket"]["expanded"]["trades"])

    def test_cell_metrics_and_minimum_cell_label(self) -> None:
        rows = [
            {
                "gross_R": 1.0 if index % 2 == 0 else -1.0,
                "exit_reason": "protective_stop" if index < 3 else "session_time_exit",
            }
            for index in range(9)
        ]
        underpowered = summarize_descriptive_cell(rows)
        eligible = summarize_descriptive_cell(rows + [rows[0]])
        required = {
            "trades",
            "net_R",
            "expectancy_R",
            "profit_factor",
            "win_rate",
            "stop_rate",
            "average_R",
            "median_R",
        }

        self.assertTrue(required.issubset(underpowered))
        self.assertEqual("underpowered_descriptive_only", underpowered["cell_status"])
        self.assertEqual(3.0 / 9.0, underpowered["stop_rate"])
        self.assertEqual("descriptive_only", eligible["cell_status"])

    def test_bound_study_runs_without_filtering_the_ledger(self) -> None:
        result = run_range_compression_study(repo_root=ROOT)
        coverage = result["assignment_coverage"]
        self.assertEqual(101, coverage["source_trade_count"])
        self.assertEqual(101, coverage["reported_trade_count"])
        self.assertFalse(coverage["trade_filtering_applied"])
        self.assertGreater(coverage["unassigned_warmup_trade_count"], 0)
        self.assertEqual(coverage["unassigned_warmup_trade_count"], coverage["unassigned_warmup_descriptive_cell"]["trades"])
        self.assertEqual(126, result["reference_width_reconstruction"]["eligible_reference_width_count"])
        self.assertEqual(
            {
                "overall",
                "by_side",
                "by_compression_bucket",
                "side_x_compression_bucket",
                "regime_x_side_x_compression_bucket",
            },
            set(result["breakdowns"]),
        )


if __name__ == "__main__":
    unittest.main()
