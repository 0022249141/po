from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import yaml

from research_core.residual_friction_budget_validation import (
    validate_repository_residual_friction_budget,
    validate_residual_friction_budget_spec,
)


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "quant" / "candidates" / "XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.residual_friction_budget.yaml"


class ResidualFrictionBudgetValidationTests(unittest.TestCase):
    def test_repository_budget_spec(self) -> None:
        result = validate_repository_residual_friction_budget(ROOT)
        self.assertEqual(result.status, "pass", result.errors)

    def test_primary_spread_tamper_is_rejected(self) -> None:
        data = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
        data["binding"]["primary_spread_points"] = 25
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", encoding="utf-8", delete=False) as handle:
            yaml.safe_dump(data, handle, sort_keys=False)
            path = Path(handle.name)
        try:
            result = validate_residual_friction_budget_spec(path, ROOT)
            self.assertEqual(result.status, "fail")
            self.assertTrue(any("primary_spread_points" in error for error in result.errors))
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
