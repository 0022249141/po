from __future__ import annotations

import unittest

from research_core.regime_result_summary import summarize_regime_result


class RegimeResultSummaryTests(unittest.TestCase):
    def test_compact_summary_extracts_regime_persistence(self) -> None:
        payload = {
            "study_id": "xauusd_named_session_tpo_regime_robustness_v1",
            "regime_robustness": {
                "regime_id": "lagged_paired_range_rank_v1",
                "paired_date_count": 120,
                "warmup_excluded_paired_dates": 20,
                "labeled_paired_date_count": 100,
                "eligible_regime_count": 3,
                "eligible_regimes": ["low", "normal", "high"],
                "regime_buckets": {
                    label: {
                        "eligible": True,
                        "counts": {"london": 30, "new_york": 30},
                        "comparison": {
                            "range_ticks": {"direction": "new_york_gt_london"},
                            "occupancy_events": {"direction": "new_york_gt_london"},
                        },
                    }
                    for label in ("low", "normal", "high")
                },
                "directional_persistence": {
                    "range_ticks": {
                        "base_direction": "new_york_gt_london",
                        "eligible_regime_count": 3,
                        "matching_direction_regime_count": 3,
                        "matching_direction_fraction": 1.0,
                    },
                    "occupancy_events": {
                        "base_direction": "new_york_gt_london",
                        "eligible_regime_count": 3,
                        "matching_direction_regime_count": 3,
                        "matching_direction_fraction": 1.0,
                    },
                },
                "statistical_significance_test": "none",
            },
        }

        summary = summarize_regime_result(payload)
        self.assertEqual(summary["paired_date_count"], 120)
        self.assertEqual(summary["eligible_regime_count"], 3)
        self.assertEqual(summary["buckets"]["normal"]["london_n"], 30)
        self.assertEqual(
            summary["directional_persistence"]["range_ticks"]["matching_direction_fraction"],
            1.0,
        )

    def test_missing_bucket_is_rejected(self) -> None:
        payload = {
            "study_id": "x",
            "regime_robustness": {
                "regime_buckets": {},
                "directional_persistence": {},
            },
        }
        with self.assertRaises(ValueError):
            summarize_regime_result(payload)


if __name__ == "__main__":
    unittest.main()
