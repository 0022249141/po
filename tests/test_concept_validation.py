from __future__ import annotations

import unittest

from research_core.concept_validation import validate_concept_registry


class ConceptRegistryValidationTests(unittest.TestCase):
    def test_repository_concept_registry(self) -> None:
        result = validate_concept_registry(".")
        self.assertEqual(result.errors, [])


if __name__ == "__main__":
    unittest.main()
