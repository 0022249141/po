import tempfile
import unittest
from pathlib import Path

from research_core.mt5_utc_bundle import (
    bar_is_closed,
    epoch_seconds_to_utc_iso,
    sha256_file,
    validate_utc_bundle_manifest,
)


class MT5UTCBundleTests(unittest.TestCase):
    def test_epoch_is_rendered_as_utc(self):
        self.assertEqual(epoch_seconds_to_utc_iso(0), "1970-01-01T00:00:00Z")

    def test_bar_close_boundary_is_causal(self):
        self.assertFalse(bar_is_closed(1000, 300, 1299.999))
        self.assertTrue(bar_is_closed(1000, 300, 1300))

    def test_valid_manifest_and_hash_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "sample.csv"
            data.write_text("x\n1\n", encoding="utf-8")
            manifest = {
                "schema_version": 1,
                "exporter": {"id": "p_mt5_utc_bundle_v1"},
                "timestamp_semantics": "utc_from_metatrader5_python_api",
                "export_time_utc": "2026-09-04T00:00:00+00:00",
                "broker": {"company": "Broker", "server": "Server"},
                "symbol": {"name": "XAUUSD_o"},
                "files": [
                    {
                        "path": "sample.csv",
                        "kind": "ohlc",
                        "rows": 1,
                        "sha256": sha256_file(data),
                    }
                ],
                "legacy_source_local_bundle_retroactively_verified": False,
            }
            result = validate_utc_bundle_manifest(manifest, root)
            self.assertEqual(result["status"], "pass", result)

    def test_hash_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = root / "sample.csv"
            data.write_text("x\n1\n", encoding="utf-8")
            manifest = {
                "schema_version": 1,
                "exporter": {"id": "p_mt5_utc_bundle_v1"},
                "timestamp_semantics": "utc_from_metatrader5_python_api",
                "export_time_utc": "2026-09-04T00:00:00+00:00",
                "broker": {"company": "Broker", "server": "Server"},
                "symbol": {"name": "XAUUSD_o"},
                "files": [
                    {
                        "path": "sample.csv",
                        "kind": "ohlc",
                        "rows": 1,
                        "sha256": "0" * 64,
                    }
                ],
                "legacy_source_local_bundle_retroactively_verified": False,
            }
            result = validate_utc_bundle_manifest(manifest, root)
            self.assertEqual(result["status"], "fail")
            self.assertTrue(any("sha256 mismatch" in item for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
