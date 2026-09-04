from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

import yaml

from research_core.regime_result_validation import validate_regime_result, validate_repository_regime_results


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "quant/results/XAUUSD_NAMED_SESSION_TPO_REGIME_ROBUSTNESS_V1.result.yaml"


class RegimeResultValidationTests(unittest.TestCase):
    def test_repository_regime_result(self) -> None:
        result = validate_repository_regime_results(ROOT)
        self.assertEqual([], result.errors)

    def test_tampered_persistence_fraction_is_rejected(self) -> None:
        payload = yaml.safe_load(RESULT.read_text(encoding="utf-8"))
        tampered = copy.deepcopy(payload)
        tampered["directional_persistence"]["range_ticks"]["matching_direction_fraction"] = 0.5
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tampered.result.yaml"
            path.write_text(yaml.safe_dump(tampered, sort_keys=False), encoding="utf-8")
            result = validate_regime_result(path, ROOT)
        self.assertTrue(any("matching_direction_fraction" in error for error in result.errors))

    def test_tampered_bucket_count_is_rejected(self) -> None:
        payload = yaml.safe_load(RESULT.read_text(encoding="utf-8"))
        tampered = copy.deepcopy(payload)
        tampered["regime_buckets"]["low"]["london_n"] = 42
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tampered.result.yaml"
            path.write_text(yaml.safe_dump(tampered, sort_keys=False), encoding="utf-8")
            result = validate_regime_result(path, ROOT)
        self.assertTrue(any("paired London/New York counts must match" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
