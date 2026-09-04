import unittest

from research_core.registry import validate_source_registry


class RegistryTests(unittest.TestCase):
    def test_repo_registry(self):
        report = validate_source_registry("config/source-registry.yaml")
        self.assertNotEqual(report["status"], "fail", report)
        self.assertGreater(report["sources"], 0)


if __name__ == "__main__":
    unittest.main()
