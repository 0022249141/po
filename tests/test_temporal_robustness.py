from __future__ import annotations

from pathlib import Path
import unittest

from research_core.temporal_robustness import summarize_temporal_feature_rows
from research_core.temporal_robustness_validation import validate_repository_temporal_robustness_specs


class TemporalRobustnessTests(unittest.TestCase):
    def test_repository_temporal_robustness_spec(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = validate_repository_temporal_robustness_specs(root)
        self.assertEqual([], result.errors)

    def test_monthly_direction_persistence_uses_eligible_buckets_only(self) -> None:
        spec = {
            "features": ["range_ticks", "occupancy_events", "bars_seen"],
            "comparison_policy": {"primary_pair": ["london", "new_york"]},
            "follow_up_design": {
                "base_observed_direction_reference": {
                    "range_ticks": "new_york_gt_london",
                    "occupancy_events": "new_york_gt_london",
                }
            },
            "temporal_robustness": {
                "bucket_basis": "session_local_start_month",
                "minimum_pair_n_per_bucket": 2,
                "directional_features": ["range_ticks", "occupancy_events"],
            },
        }
        rows = {
            "london": [
                {"session_instance_id": "london:2026-03-02", "range_ticks": 10, "occupancy_events": 100, "bars_seen": 108},
                {"session_instance_id": "london:2026-03-03", "range_ticks": 12, "occupancy_events": 110, "bars_seen": 108},
                {"session_instance_id": "london:2026-04-01", "range_ticks": 20, "occupancy_events": 200, "bars_seen": 108},
            ],
            "new_york": [
                {"session_instance_id": "new_york:2026-03-02", "range_ticks": 14, "occupancy_events": 120, "bars_seen": 108},
                {"session_instance_id": "new_york:2026-03-03", "range_ticks": 16, "occupancy_events": 130, "bars_seen": 108},
                {"session_instance_id": "new_york:2026-04-01", "range_ticks": 18, "occupancy_events": 190, "bars_seen": 108},
            ],
        }

        result = summarize_temporal_feature_rows(rows, spec)
        self.assertEqual(["2026-03"], result["eligible_buckets"])
        self.assertTrue(result["month_buckets"]["2026-03"]["eligible"])
        self.assertFalse(result["month_buckets"]["2026-04"]["eligible"])
        self.assertEqual(
            "new_york_gt_london",
            result["month_buckets"]["2026-03"]["comparison"]["range_ticks"]["direction"],
        )
        self.assertEqual(
            1.0,
            result["directional_persistence"]["range_ticks"]["matching_direction_fraction"],
        )


if __name__ == "__main__":
    unittest.main()
