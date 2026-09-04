import json
import tempfile
import unittest
from pathlib import Path

from research_core.canonical_dataset import build_promotion_record, canonical_dataset_id
from research_core.mt5_utc_bundle import sha256_file


class CanonicalDatasetTests(unittest.TestCase):
    def _make_bundle(self, root: Path, *, exporter_id: str = "p_mt5_utc_bundle_v1") -> Path:
        data = root / "XAUUSD_o_M5_bars_utc.csv"
        data.write_text("time_utc,open\n2026-09-04T06:00:00Z,4400\n", encoding="utf-8")
        manifest = {
            "schema_version": 1,
            "exporter": {"id": exporter_id, "version": "1.0.0", "read_only": True},
            "timestamp_semantics": "utc_from_metatrader5_python_api",
            "export_time_utc": "2026-09-04T06:01:26+00:00",
            "broker": {"company": "LiteFinance Global LLC", "server": "LiteFinance-MT5-Live"},
            "terminal": {"version": [5, 0, 6030], "connected": True},
            "symbol": {"name": "XAUUSD_o"},
            "files": [
                {
                    "path": data.name,
                    "kind": "ohlc",
                    "timeframe": "M5",
                    "rows": 1,
                    "first_time_utc": "2026-09-04T06:00:00Z",
                    "last_time_utc": "2026-09-04T06:00:00Z",
                    "sha256": sha256_file(data),
                }
            ],
            "binding_scope": "newly_generated_files_in_this_bundle_only",
            "legacy_source_local_bundle_retroactively_verified": False,
        }
        path = root / "binding_manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        return path

    def test_dataset_id_is_deterministic(self):
        manifest = {
            "symbol": {"name": "XAUUSD_o"},
            "export_time_utc": "2026-09-04T06:01:26+00:00",
        }
        self.assertEqual(canonical_dataset_id(manifest), "xauusd_o_mt5_utc_20260904_060126")

    def test_valid_bundle_becomes_verified_utc_promotion_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._make_bundle(Path(tmp))
            record = build_promotion_record(path)
            self.assertEqual(record["status"], "verified")
            self.assertEqual(record["timebase"]["source_timezone"], "UTC")
            self.assertTrue(record["timebase"]["named_session_use_allowed"])
            self.assertEqual(
                record["session_policy_authorization"]["policy_id"],
                "xauusd_major_fx_sessions_v1",
            )
            self.assertEqual(record["validation"]["status"], "pass")

    def test_wrong_exporter_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self._make_bundle(Path(tmp), exporter_id="unknown")
            with self.assertRaisesRegex(ValueError, "exporter.id"):
                build_promotion_record(path)


if __name__ == "__main__":
    unittest.main()
