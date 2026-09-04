from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import yaml

from research_core.temporal_result_validation import validate_repository_temporal_results, validate_temporal_result


class TemporalResultValidationTests(unittest.TestCase):
    def test_repository_temporal_result(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = validate_repository_temporal_results(root)
        self.assertEqual([], result.errors)

    def test_tampered_persistence_fraction_is_rejected(self) -> None:
        root = Path(__file__).resolve().parents[1]
        source = root / "quant/results/XAUUSD_NAMED_SESSION_TPO_TEMPORAL_ROBUSTNESS_V1.result.yaml"
        data = yaml.safe_load(source.read_text(encoding="utf-8"))
        data["persistence"]["range_ticks"]["matching_direction_fraction"] = 0.5
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tampered.result.yaml"
            path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
            result = validate_temporal_result(path, root)
            self.assertTrue(any("matching-direction fraction" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
