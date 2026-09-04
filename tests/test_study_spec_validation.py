from __future__ import annotations

import unittest
from pathlib import Path

from research_core.study_spec_validation import validate_repository_study_specs


class StudySpecValidationTests(unittest.TestCase):
    def test_repository_study_specs(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = validate_repository_study_specs(root)
        self.assertEqual([], result.errors)
        self.assertEqual("pass", result.status)


if __name__ == "__main__":
    unittest.main()
