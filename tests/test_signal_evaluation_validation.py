from __future__ import annotations

from pathlib import Path
import copy
import unittest

import yaml

from research_core.signal_evaluation_validation import validate_signal_evaluation_document, validate_signal_evaluation_file


ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "quant" / "candidates" / "XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.evaluation.yaml"


class SignalEvaluationValidationTests(unittest.TestCase):
    def test_repository_evaluation_spec(self) -> None:
        result = validate_signal_evaluation_file(EVAL, ROOT)
        self.assertEqual(result.errors, [])

    def test_cost_application_tamper_is_rejected(self) -> None:
        doc = yaml.safe_load(EVAL.read_text(encoding="utf-8"))
        tampered = copy.deepcopy(doc)
        tampered["cost_model"]["spread_applied"] = True
        result = validate_signal_evaluation_document(tampered, ROOT)
        self.assertTrue(any("spread_applied" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
