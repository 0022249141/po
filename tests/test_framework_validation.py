from __future__ import annotations

import unittest

from research_core.framework_validation import validate_framework_ingestion


class FrameworkIngestionValidationTests(unittest.TestCase):
    def test_repository_framework_status(self) -> None:
        result = validate_framework_ingestion(".")
        self.assertEqual(result.errors, [])


if __name__ == "__main__":
    unittest.main()
