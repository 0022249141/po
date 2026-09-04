from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import yaml

from research_core.study_result_validation import (
    validate_repository_study_results,
    validate_study_result,
)


ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = ROOT / "quant" / "results" / "XAUUSD_NAMED_SESSION_TPO_DESCRIPTIVE_V1.result.yaml"


class StudyResultValidationTests(unittest.TestCase):
    def test_repository_study_results(self) -> None:
        result = validate_repository_study_results(ROOT)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])

    def test_tampered_primary_ratio_is_rejected(self) -> None:
        payload = yaml.safe_load(RESULT_PATH.read_text(encoding="utf-8"))
        payload["primary_comparison"]["range_ticks"]["median_ratio_left_over_right"] = 9.99

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tampered.result.yaml"
            path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
            result = validate_study_result(path, ROOT)

        self.assertTrue(any("range_ticks: median ratio" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
