from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

import yaml

from research_core.spread_sensitivity_validation import validate_repository_spread_sensitivity, validate_spread_sensitivity_spec


class SpreadSensitivityValidationTests(unittest.TestCase):
    def test_repository_spread_sensitivity_spec(self):
        result = validate_repository_spread_sensitivity(".")
        self.assertEqual(result.errors, [])

    def test_scenario_tamper_is_rejected(self):
        source = Path("quant/candidates/XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.spread_sensitivity.yaml")
        doc = yaml.safe_load(source.read_text(encoding="utf-8"))
        tampered = copy.deepcopy(doc)
        tampered["scenarios"][1]["spread_points"] = 23
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "spec.yaml"
            path.write_text(yaml.safe_dump(tampered, sort_keys=False), encoding="utf-8")
            result = validate_spread_sensitivity_spec(path, ".")
        self.assertTrue(any("spread scenarios" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
