import unittest
from datetime import date, datetime, timezone
from pathlib import Path

from research_core.session_policy import NamedSessionPolicy, validate_session_policy_file


UTC = timezone.utc
POLICY_PATH = Path("config/session-policies/xauusd-major-sessions.yaml")


class NamedSessionPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = NamedSessionPolicy.from_yaml(POLICY_PATH)

    def test_repository_policy_validates(self):
        result = validate_session_policy_file(POLICY_PATH)
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.errors, [])

    def test_tokyo_stays_fixed_in_utc_across_seasons(self):
        jan_start, jan_end = self.policy.bounds_utc("asia_tokyo", date(2026, 1, 15))
        jul_start, jul_end = self.policy.bounds_utc("asia_tokyo", date(2026, 7, 15))
        self.assertEqual(jan_start, datetime(2026, 1, 15, 0, 0, tzinfo=UTC))
        self.assertEqual(jan_end, datetime(2026, 1, 15, 9, 0, tzinfo=UTC))
        self.assertEqual(jul_start, datetime(2026, 7, 15, 0, 0, tzinfo=UTC))
        self.assertEqual(jul_end, datetime(2026, 7, 15, 9, 0, tzinfo=UTC))

    def test_london_dst_changes_utc_boundary(self):
        jan_start, jan_end = self.policy.bounds_utc("london", date(2026, 1, 15))
        jul_start, jul_end = self.policy.bounds_utc("london", date(2026, 7, 15))
        self.assertEqual(jan_start, datetime(2026, 1, 15, 8, 0, tzinfo=UTC))
        self.assertEqual(jan_end, datetime(2026, 1, 15, 17, 0, tzinfo=UTC))
        self.assertEqual(jul_start, datetime(2026, 7, 15, 7, 0, tzinfo=UTC))
        self.assertEqual(jul_end, datetime(2026, 7, 15, 16, 0, tzinfo=UTC))

    def test_new_york_dst_changes_utc_boundary(self):
        jan_start, jan_end = self.policy.bounds_utc("new_york", date(2026, 1, 15))
        jul_start, jul_end = self.policy.bounds_utc("new_york", date(2026, 7, 15))
        self.assertEqual(jan_start, datetime(2026, 1, 15, 13, 0, tzinfo=UTC))
        self.assertEqual(jan_end, datetime(2026, 1, 15, 22, 0, tzinfo=UTC))
        self.assertEqual(jul_start, datetime(2026, 7, 15, 12, 0, tzinfo=UTC))
        self.assertEqual(jul_end, datetime(2026, 7, 15, 21, 0, tzinfo=UTC))

    def test_us_uk_dst_mismatch_week_is_not_flattened(self):
        london_start, _ = self.policy.bounds_utc("london", date(2026, 3, 16))
        new_york_start, _ = self.policy.bounds_utc("new_york", date(2026, 3, 16))
        self.assertEqual(london_start, datetime(2026, 3, 16, 8, 0, tzinfo=UTC))
        self.assertEqual(new_york_start, datetime(2026, 3, 16, 12, 0, tzinfo=UTC))

    def test_start_inclusive_end_exclusive(self):
        self.assertTrue(self.policy.contains("london", datetime(2026, 7, 15, 7, 0, tzinfo=UTC)))
        self.assertTrue(self.policy.contains("london", datetime(2026, 7, 15, 15, 59, tzinfo=UTC)))
        self.assertFalse(self.policy.contains("london", datetime(2026, 7, 15, 16, 0, tzinfo=UTC)))

    def test_overlaps_are_preserved(self):
        self.assertEqual(
            self.policy.classify(datetime(2026, 7, 15, 12, 0, tzinfo=UTC)),
            ["london", "new_york"],
        )
        self.assertEqual(
            self.policy.classify(datetime(2026, 7, 15, 7, 30, tzinfo=UTC)),
            ["asia_tokyo", "london"],
        )

    def test_session_instance_uses_local_start_date(self):
        instance = self.policy.session_instance_id(
            "new_york", datetime(2026, 7, 15, 12, 0, tzinfo=UTC)
        )
        self.assertEqual(instance, "new_york:2026-07-15")


if __name__ == "__main__":
    unittest.main()
