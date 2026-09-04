from __future__ import annotations

import unittest

from research_core.operationalization_validation import validate_operationalization


class OperationalizationValidationTests(unittest.TestCase):
    def test_repository_operationalization_registry(self) -> None:
        result = validate_operationalization(".")
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.status, "pass")


if __name__ == "__main__":
    unittest.main()
