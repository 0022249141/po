from __future__ import annotations

import unittest

from research_core.timebase_validation import validate_timebase_document, validate_timebase_registry


BASE_RULES = {
    "verified_requires_non_statistical_evidence": True,
    "statistical_inference_alone_cannot_verify": True,
    "named_session_use_requires_verified": True,
    "no_timezone_inference_from_filename": True,
    "no_timezone_inference_from_gap_pattern_alone": True,
}


class TimebaseValidationTests(unittest.TestCase):
    def test_repository_timebase_registry(self) -> None:
        result = validate_timebase_registry(".")
        self.assertEqual(result.errors, [])
        self.assertEqual(result.status, "pass")

    def test_unresolved_cannot_authorize_named_sessions(self) -> None:
        doc = {
            "datasets": {
                "x": {
                    "source_id": "user_mt5_export",
                    "status": "unresolved",
                    "source_timestamp_semantics": "source_local_unknown_timezone",
                    "named_session_use_allowed": True,
                    "neutral_policy": "source_calendar_day_v1",
                    "evidence": [],
                    "blockers": ["timezone unresolved"],
                }
            },
            "rules": dict(BASE_RULES),
        }
        result = validate_timebase_document(doc)
        self.assertEqual(result.status, "fail")
        self.assertTrue(any("named session" in error for error in result.errors))

    def test_statistical_inference_alone_cannot_verify(self) -> None:
        doc = {
            "datasets": {
                "x": {
                    "source_id": "user_mt5_export",
                    "status": "verified",
                    "source_timestamp_semantics": "source_local",
                    "source_timezone": "Etc/GMT-3",
                    "dst_policy": "none",
                    "broker_feed_identity": "example",
                    "named_session_use_allowed": True,
                    "evidence": [
                        {
                            "type": "statistical_inference",
                            "provenance": "recurring daily gap pattern",
                        }
                    ],
                    "blockers": [],
                }
            },
            "rules": dict(BASE_RULES),
        }
        result = validate_timebase_document(doc)
        self.assertEqual(result.status, "fail")
        self.assertTrue(any("non-statistical" in error for error in result.errors))


if __name__ == "__main__":
    unittest.main()
