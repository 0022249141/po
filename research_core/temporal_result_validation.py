from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import math

import yaml

from .study_result_validation import validate_study_result


REQUIRED_BOUNDARIES = (
    "descriptive_only",
    "trading_signal_prohibited",
    "profitability_claim_prohibited",
    "poc_value_area_prohibited",
    "ict_kill_zone_substitution_prohibited",
    "centralized_volume_claim_prohibited",
    "dealer_inventory_claim_prohibited",
    "statistical_significance_not_tested",
    "regime_conditioning_not_tested",
)


@dataclass(frozen=True)
class TemporalResultValidationResult:
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


def _same_number(left: Any, right: Any, *, rel_tol: float = 1e-12, abs_tol: float = 1e-12) -> bool:
    try:
        return math.isclose(float(left), float(right), rel_tol=rel_tol, abs_tol=abs_tol)
    except (TypeError, ValueError):
        return False


def _direction(left: float, right: float) -> str:
    if math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12):
        return "tie"
    return "london_gt_new_york" if left > right else "new_york_gt_london"


def validate_temporal_result(result_path: str | Path, repo_root: str | Path = ".") -> TemporalResultValidationResult:
    root = Path(repo_root)
    path = Path(result_path)
    if not path.is_absolute():
        path = root / path

    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        return TemporalResultValidationResult([f"missing: {path}"], warnings)
    try:
        result = _load_yaml(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return TemporalResultValidationResult([str(exc)], warnings)

    if result.get("status") != "recorded":
        errors.append("result status must be recorded")
    if result.get("result_type") != "compact_temporal_robustness_result":
        errors.append("result_type must be compact_temporal_robustness_result")

    provenance = result.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance must be a mapping")
    else:
        if provenance.get("raw_result_committed") is not False:
            errors.append("raw_result_committed must be false")
        if not provenance.get("execution_command"):
            errors.append("provenance.execution_command is required")
        if not provenance.get("raw_result_path_external"):
            errors.append("provenance.raw_result_path_external is required")

    binding = result.get("study_binding")
    if not isinstance(binding, dict):
        return TemporalResultValidationResult(errors + ["study_binding must be a mapping"], warnings)

    spec_rel = binding.get("spec_path")
    if not spec_rel:
        return TemporalResultValidationResult(errors + ["study_binding.spec_path is required"], warnings)
    spec_path = root / str(spec_rel)
    if not spec_path.exists():
        return TemporalResultValidationResult(errors + [f"missing spec: {spec_rel}"], warnings)
    try:
        spec = _load_yaml(spec_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return TemporalResultValidationResult(errors + [str(exc)], warnings)

    if spec.get("status") != "frozen":
        errors.append("bound temporal specification must be frozen")
    if result.get("study_id") != spec.get("study_id"):
        errors.append("result study_id does not match bound specification")

    data = spec.get("data", {})
    session = spec.get("session_context", {})
    selection = session.get("selection", {}) if isinstance(session, dict) else {}
    op = spec.get("operational_input", {})
    follow = spec.get("follow_up_design", {})
    temporal = spec.get("temporal_robustness", {})

    expected_bindings = {
        "spec_status": spec.get("status"),
        "declared_follow_up": True,
        "base_study_id": follow.get("base_study_id"),
        "base_result_path": follow.get("base_result_path"),
        "dataset_id": data.get("dataset_id"),
        "dataset_manifest": data.get("dataset_manifest"),
        "timeframe": data.get("timeframe"),
        "cutoff_utc": data.get("cutoff_utc"),
        "session_policy_id": session.get("policy_id"),
        "completeness_mode": selection.get("completeness_mode"),
        "exclude_coverage_edges": selection.get("exclude_coverage_edges"),
        "operational_rule_id": op.get("rule_id"),
        "price_increment": str(op.get("price_increment")),
        "bucket_basis": temporal.get("bucket_basis"),
        "minimum_pair_n_per_bucket": temporal.get("minimum_pair_n_per_bucket"),
        "statistical_significance_test": temporal.get("statistical_significance_test"),
        "regime_labels": temporal.get("regime_labels"),
    }
    for key, expected in expected_bindings.items():
        actual = binding.get(key)
        if key == "price_increment":
            if str(actual) != str(expected):
                errors.append(f"study_binding.{key} does not match specification")
        elif actual != expected:
            errors.append(f"study_binding.{key} does not match specification")

    base_rel = follow.get("base_result_path")
    if base_rel:
        base_validation = validate_study_result(root / str(base_rel), root)
        errors.extend(f"base result: {message}" for message in base_validation.errors)

    months = result.get("monthly_buckets")
    if not isinstance(months, dict) or not months:
        return TemporalResultValidationResult(errors + ["monthly_buckets must be a non-empty mapping"], warnings)

    minimum_n = int(temporal.get("minimum_pair_n_per_bucket", 0))
    eligible_months: list[str] = []
    directional_features = list(temporal.get("directional_features") or [])
    base_reference = follow.get("base_observed_direction_reference", {})

    for month, record in sorted(months.items()):
        if not isinstance(record, dict):
            errors.append(f"{month}: bucket must be a mapping")
            continue
        try:
            london_n = int(record.get("london_n"))
            new_york_n = int(record.get("new_york_n"))
        except (TypeError, ValueError):
            errors.append(f"{month}: session counts must be integers")
            continue
        expected_eligible = london_n >= minimum_n and new_york_n >= minimum_n
        if record.get("eligible") is not expected_eligible:
            errors.append(f"{month}: eligible flag disagrees with minimum-pair-n rule")
        if expected_eligible:
            eligible_months.append(str(month))

        for feature in directional_features:
            feature_record = record.get(feature)
            if not isinstance(feature_record, dict):
                errors.append(f"{month}: missing directional feature {feature}")
                continue
            left = feature_record.get("london_median")
            right = feature_record.get("new_york_median")
            try:
                left_f = float(left)
                right_f = float(right)
            except (TypeError, ValueError):
                errors.append(f"{month} {feature}: medians must be numeric")
                continue
            expected_diff = left_f - right_f
            if not _same_number(feature_record.get("median_difference_left_minus_right"), expected_diff):
                errors.append(f"{month} {feature}: median difference inconsistent with medians")
            expected_direction = _direction(left_f, right_f)
            if feature_record.get("direction") != expected_direction:
                errors.append(f"{month} {feature}: direction inconsistent with medians")

    persistence = result.get("persistence")
    if not isinstance(persistence, dict):
        errors.append("persistence must be a mapping")
    else:
        recorded_eligible = list(persistence.get("eligible_buckets") or [])
        if recorded_eligible != eligible_months:
            errors.append("persistence.eligible_buckets does not match recomputed eligible buckets")
        if int(persistence.get("eligible_bucket_count", -1)) != len(eligible_months):
            errors.append("persistence.eligible_bucket_count is inconsistent")

        for feature in directional_features:
            record = persistence.get(feature)
            if not isinstance(record, dict):
                errors.append(f"persistence missing feature {feature}")
                continue
            expected_base = str(base_reference.get(feature))
            if record.get("base_direction") != expected_base:
                errors.append(f"persistence {feature}: base direction does not match specification")
            matches = 0
            for month in eligible_months:
                feature_record = months.get(month, {}).get(feature, {})
                if feature_record.get("direction") == expected_base:
                    matches += 1
            if int(record.get("matching_direction_bucket_count", -1)) != matches:
                errors.append(f"persistence {feature}: matching-direction count is inconsistent")
            expected_fraction = matches / len(eligible_months) if eligible_months else None
            actual_fraction = record.get("matching_direction_fraction")
            if expected_fraction is None:
                if actual_fraction is not None:
                    errors.append(f"persistence {feature}: fraction must be null without eligible buckets")
            elif not _same_number(actual_fraction, expected_fraction):
                errors.append(f"persistence {feature}: matching-direction fraction is inconsistent")

    boundaries = result.get("interpretation_boundaries")
    if not isinstance(boundaries, dict):
        errors.append("interpretation_boundaries must be a mapping")
    else:
        for key in REQUIRED_BOUNDARIES:
            if boundaries.get(key) is not True:
                errors.append(f"interpretation boundary {key} must remain true")

    return TemporalResultValidationResult(errors, warnings)


def validate_repository_temporal_results(repo_root: str | Path = ".") -> TemporalResultValidationResult:
    root = Path(repo_root)
    result_dir = root / "quant" / "results"
    paths = sorted(result_dir.glob("*TEMPORAL_ROBUSTNESS*.result.yaml"))
    if not paths:
        return TemporalResultValidationResult(["no temporal robustness result YAML files found"], [])
    errors: list[str] = []
    warnings: list[str] = []
    for path in paths:
        result = validate_temporal_result(path, root)
        errors.extend(f"{path.name}: {message}" for message in result.errors)
        warnings.extend(f"{path.name}: {message}" for message in result.warnings)
    return TemporalResultValidationResult(errors, warnings)


def format_result(result: TemporalResultValidationResult) -> dict[str, object]:
    return {"status": result.status, "errors": result.errors, "warnings": result.warnings}
