from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

import yaml

from research_core.strategy_spec_validation import validate_strategy_spec


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "quant" / "candidates" / "XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.strategy.yaml"


class StrategySpecValidationTests(unittest.TestCase):
    def test_repository_strategy_spec_validates(self) -> None:
        result = validate_strategy_spec(SPEC, ROOT)
        self.assertEqual(result.status, "pass", result.errors)

    def test_regime_filter_tamper_is_rejected(self) -> None:
        payload = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
        tampered = deepcopy(payload)
        tampered["regime_context"]["allowed_as_entry_filter"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tampered.strategy.yaml"
            path.write_text(yaml.safe_dump(tampered, sort_keys=False), encoding="utf-8")
            result = validate_strategy_spec(path, ROOT)
        self.assertEqual(result.status, "fail")
        self.assertTrue(any("must not filter" in error for error in result.errors))

    def test_same_bar_fill_tamper_is_rejected(self) -> None:
        payload = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
        tampered = deepcopy(payload)
        tampered["entry"]["fill_timing"] = "trigger_bar_close"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tampered.strategy.yaml"
            path.write_text(yaml.safe_dump(tampered, sort_keys=False), encoding="utf-8")
            result = validate_strategy_spec(path, ROOT)
        self.assertEqual(result.status, "fail")
        self.assertTrue(any("fill_timing" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
