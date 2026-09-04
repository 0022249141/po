from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import json
import yaml


@dataclass(frozen=True)
class SpreadSensitivityValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def status(self) -> str:
        return "pass" if not self.errors else "fail"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def validate_spread_sensitivity_spec(path: str | Path, repo_root: str | Path = ".") -> SpreadSensitivityValidationResult:
    root = Path(repo_root)
    spec_path = Path(path)
    if not spec_path.is_absolute():
        spec_path = root / spec_path
    errors: list[str] = []
    warnings: list[str] = []
    if not spec_path.exists():
        return SpreadSensitivityValidationResult([f"missing: {spec_path}"], warnings)
    try:
        spec = _load_yaml(spec_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return SpreadSensitivityValidationResult([str(exc)], warnings)

    if spec.get("status") != "frozen":
        errors.append("status must be frozen")
    if spec.get("sensitivity_class") != "post_gross_fixed_spread_deduction":
        errors.append("unexpected sensitivity_class")

    binding = spec.get("binding")
    if not isinstance(binding, dict):
        return SpreadSensitivityValidationResult(errors + ["binding must be a mapping"], warnings)
    for key in ("strategy_spec_path", "evaluation_spec_path", "gross_result_path", "dataset_manifest"):
        rel = binding.get(key)
        if not rel or not (root / str(rel)).exists():
            errors.append(f"binding.{key} must reference an existing file")
    if binding.get("dataset_id") != "xauusd_o_utc_20260904_052959":
        errors.append("dataset_id must remain canonical")
    if float(binding.get("point_size", -1)) != 0.01:
        errors.append("point_size must remain 0.01")

    manifest_path = root / str(binding.get("dataset_manifest", ""))
    manifest: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(str(exc))
    tick_quality = manifest.get("qualification", {}).get("tick_quality", {}) if manifest else {}

    evidence = spec.get("spread_evidence")
    if not isinstance(evidence, dict):
        errors.append("spread_evidence must be a mapping")
        evidence = {}
    expected_spreads = {
        "observed_spread_points_min": tick_quality.get("spread_points_min"),
        "observed_spread_points_median": tick_quality.get("spread_points_median"),
        "observed_spread_points_max": tick_quality.get("spread_points_max"),
    }
    for key, expected in expected_spreads.items():
        if evidence.get(key) != expected:
            errors.append(f"spread_evidence.{key} must match canonical manifest")
    if evidence.get("historical_full_sample_spread_calibration_available") is not False:
        errors.append("full-sample historical spread calibration must remain false")

    side = spec.get("bar_side_semantics")
    if not isinstance(side, dict):
        errors.append("bar_side_semantics must be a mapping")
    else:
        if side.get("classification") != "bid_like_for_sensitivity_only":
            errors.append("bar side classification must remain sensitivity-only")
        if side.get("exact_historical_execution_claim_prohibited") is not True:
            errors.append("exact historical execution claims must remain prohibited")

    scenarios = spec.get("scenarios")
    expected = [
        ("observed_min_fixed", 12, "sensitivity"),
        ("observed_median_fixed", 22, "primary_gate"),
        ("observed_max_fixed", 151, "stress_only"),
    ]
    if not isinstance(scenarios, list) or len(scenarios) != 3:
        errors.append("exactly three frozen spread scenarios are required")
    else:
        actual = [(str(x.get("id")), int(x.get("spread_points")), str(x.get("role"))) for x in scenarios if isinstance(x, dict)]
        if actual != expected:
            errors.append("spread scenarios do not match frozen min/median/max grid")

    application = spec.get("application")
    if not isinstance(application, dict):
        errors.append("application must be a mapping")
    else:
        expected_app = {
            "method": "posthoc_single_full_spread_deduction_per_round_trip",
            "signal_path_recomputed": False,
            "stop_path_recomputed_with_ask": False,
            "commission_applied": False,
            "slippage_applied": False,
        }
        for key, expected_value in expected_app.items():
            if application.get(key) != expected_value:
                errors.append(f"application.{key} does not match frozen sensitivity semantics")

    gate = spec.get("pre_frozen_gate")
    if not isinstance(gate, dict):
        errors.append("pre_frozen_gate must be a mapping")
    else:
        if gate.get("primary_scenario") != "observed_median_fixed":
            errors.append("primary gate scenario must remain observed_median_fixed")
        if float(gate.get("expectancy_R_must_be_greater_than", -1)) != 0.0:
            errors.append("expectancy threshold must remain 0.0")
        if float(gate.get("profit_factor_must_be_greater_than", -1)) != 1.0:
            errors.append("profit factor threshold must remain 1.0")
        if gate.get("failure_action") != "do_not_tune_signal_rules":
            errors.append("failure action must prohibit signal tuning")

    boundaries = spec.get("interpretation_boundaries")
    required_true = (
        "fixed_spread_sensitivity_only",
        "not_historical_spread_calibration",
        "not_full_execution_path_backtest",
        "commission_unresolved",
        "slippage_unresolved",
        "net_profitability_not_established",
        "live_trading_prohibited",
        "signal_rule_changes_prohibited",
    )
    if not isinstance(boundaries, dict):
        errors.append("interpretation_boundaries must be a mapping")
    else:
        for key in required_true:
            if boundaries.get(key) is not True:
                errors.append(f"interpretation boundary {key} must remain true")

    return SpreadSensitivityValidationResult(errors, warnings)


def validate_repository_spread_sensitivity(repo_root: str | Path = ".") -> SpreadSensitivityValidationResult:
    root = Path(repo_root)
    paths = sorted((root / "quant" / "candidates").glob("*.spread_sensitivity.yaml"))
    if not paths:
        return SpreadSensitivityValidationResult(["no spread sensitivity specification files found"], [])
    errors: list[str] = []
    warnings: list[str] = []
    for path in paths:
        result = validate_spread_sensitivity_spec(path, root)
        errors.extend(f"{path.name}: {message}" for message in result.errors)
        warnings.extend(f"{path.name}: {message}" for message in result.warnings)
    return SpreadSensitivityValidationResult(errors, warnings)


def format_result(result: SpreadSensitivityValidationResult) -> dict[str, object]:
    return {"status": result.status, "errors": result.errors, "warnings": result.warnings}
