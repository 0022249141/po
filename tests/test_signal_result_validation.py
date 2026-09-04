from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

import yaml

from research_core.signal_result_validation import validate_repository_signal_results, validate_signal_result


class SignalResultValidationTests(unittest.TestCase):
    def test_repository_signal_result(self):
        result = validate_repository_signal_results(".")
        self.assertEqual(result.errors, [])

    def test_tampered_trade_count_is_rejected(self):
        source = Path("quant/results/XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.gross.result.yaml")
        doc = yaml.safe_load(source.read_text(encoding="utf-8"))
        tampered = copy.deepcopy(doc)
        tampered["sample"]["trade_count"] = 999
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.yaml"
            path.write_text(yaml.safe_dump(tampered, sort_keys=False), encoding="utf-8")
            result = validate_signal_result(path, ".")
        self.assertTrue(any("trade_count must equal" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
