from __future__ import annotations

import copy
from shutil import copy2
import tempfile
import unittest
from pathlib import Path

import yaml

from research_core.range_compression_study_validation import (
    validate_range_compression_study_spec,
    validate_repository_range_compression_study_specs,
)
from research_core.study_spec_validation import validate_study_spec


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "quant/studies/XAUUSD_NY_PREOPEN_RANGE_COMPRESSION_EXPLORATORY_V1.yaml"


class RangeCompressionStudyValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))

    def _validate_tampered(self, mutate) -> list[str]:
        payload = copy.deepcopy(self.spec)
        mutate(payload)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tampered.study.yaml"
            path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
            return validate_range_compression_study_spec(path, ROOT).errors

    def test_repository_study_spec_and_generic_dispatch_pass(self) -> None:
        result = validate_repository_range_compression_study_specs(ROOT)
        self.assertEqual([], result.errors)
        generic = validate_study_spec(SPEC, ROOT)
        self.assertEqual([], generic.errors)

    def test_current_day_leakage_is_rejected(self) -> None:
        errors = self._validate_tampered(
            lambda payload: payload["causal_features"]["lagged_baseline"].__setitem__("current_date_in_baseline", True)
        )
        self.assertTrue(any("current_date_in_baseline" in error for error in errors))

    def test_centered_windows_and_negative_shifts_are_rejected(self) -> None:
        centered_errors = self._validate_tampered(
            lambda payload: payload["causal_features"]["lagged_baseline"].__setitem__("centered_window", True)
        )
        negative_shift_errors = self._validate_tampered(
            lambda payload: payload["causal_features"]["lagged_baseline"].__setitem__("shift_direction", "negative")
        )
        self.assertTrue(any("centered_window" in error for error in centered_errors))
        self.assertTrue(any("shift_direction" in error for error in negative_shift_errors))

    def test_frozen_strategy_mutation_binding_is_rejected(self) -> None:
        errors = self._validate_tampered(
            lambda payload: payload["source_binding"].__setitem__("strategy_spec_sha256", "0" * 64)
        )
        self.assertTrue(any("strategy_spec_sha256" in error for error in errors))

    def test_actual_frozen_strategy_content_mutation_is_rejected(self) -> None:
        relative_paths = (
            "quant/studies/XAUUSD_NY_PREOPEN_RANGE_COMPRESSION_EXPLORATORY_V1.yaml",
            "quant/candidates/XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.strategy.yaml",
            "quant/candidates/XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.evaluation.yaml",
            "data/manifests/XAUUSD_o_UTC_20260904_052959.json",
            "MT5_UTC_EXPORTS/XAUUSD_o_20260904_052959_UTC/strategy_signal_backtest_v1.json",
            "MT5_UTC_EXPORTS/XAUUSD_o_20260904_052959_UTC/XAUUSD_o_M5_bars_utc.csv",
        )
        with tempfile.TemporaryDirectory() as tmp:
            replica = Path(tmp)
            for relative in relative_paths:
                destination = replica / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                copy2(ROOT / relative, destination)
            strategy_path = replica / "quant/candidates/XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.strategy.yaml"
            strategy_path.write_text(
                strategy_path.read_text(encoding="utf-8") + "\n# deliberate validation-fixture mutation\n",
                encoding="utf-8",
            )
            errors = validate_range_compression_study_spec(
                replica / "quant/studies/XAUUSD_NY_PREOPEN_RANGE_COMPRESSION_EXPLORATORY_V1.yaml",
                replica,
            ).errors
        self.assertTrue(any("frozen strategy SHA256" in error for error in errors))

    def test_unbound_dataset_and_backtest_artifact_are_rejected(self) -> None:
        dataset_errors = self._validate_tampered(
            lambda payload: payload["data"].__setitem__("dataset_id", "unbound_dataset")
        )
        artifact_errors = self._validate_tampered(
            lambda payload: payload.__setitem__("source_backtest_sha256", "0" * 64)
        )
        self.assertTrue(any("dataset_id" in error for error in dataset_errors))
        self.assertTrue(any("source_backtest_sha256" in error for error in artifact_errors))

    def test_undeclared_or_changed_bucket_thresholds_are_rejected(self) -> None:
        errors = self._validate_tampered(
            lambda payload: payload["causal_features"]["frozen_descriptive_buckets"]["thresholds"].pop(
                "normal_upper_exclusive"
            )
        )
        self.assertTrue(any("frozen_descriptive_buckets.thresholds" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
