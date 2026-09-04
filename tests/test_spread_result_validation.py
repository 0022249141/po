from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import yaml

from research_core.spread_result_validation import validate_repository_spread_results, validate_spread_result


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "quant" / "results" / "XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.spread.result.yaml"


class SpreadResultValidationTests(unittest.TestCase):
    def test_repository_spread_result(self) -> None:
        result = validate_repository_spread_results(ROOT)
        self.assertEqual(result.status, "pass", result.errors)

    def test_tampered_primary_gate_is_rejected(self) -> None:
        data = yaml.safe_load(RESULT.read_text(encoding="utf-8"))
        data["primary_gate"]["passed"] = False
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", encoding="utf-8", delete=False) as handle:
            yaml.safe_dump(data, handle, sort_keys=False)
            path = Path(handle.name)
        try:
            result = validate_spread_result(path, ROOT)
            self.assertEqual(result.status, "fail")
            self.assertTrue(any("primary_gate.passed" in error for error in result.errors))
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
