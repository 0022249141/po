from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import math

import yaml


REQUIRED_INTERPRETATION_BOUNDARIES = (
    "descriptive_only",
    "trading_signal_prohibited",
    "profitability_claim_prohibited",
    "poc_value_area_prohibited",
    "ict_kill_zone_substitution_prohibited",
    "centralized_volume_claim_prohibited",
    "dealer_inventory_claim_prohibited",
)


@dataclass(frozen=True)
class StudyResultValidationResult:
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


def validate_study_result(result_path: str | Path, repo_root: str | Path = ".") -> StudyResultValidationResult:
    root = Path(repo_root)
    path = Path(result_path)
    if not path.is_absolute():
        path = root / path

    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        return StudyResultValidationResult([f"missing: {path}"], warnings)

    try:
        result = _load_yaml(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return StudyResultValidationResult([str(exc)], warnings)

    if result.get("status") != "recorded":
        errors.append("result status must be recorded")
    if result.get("result_type") != "compact_descriptive_result":
        errors.append("result_type must be compact_descriptive_result")

    provenance = result.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance must be a mapping")
    else:
        if provenance.get("raw_result_committed") is not False:
            errors.append("raw_result_committed must be false for external market-data execution")
        if not provenance.get("execution_command"):
            errors.append("provenance.execution_command is required")
        if not provenance.get("raw_result_path_external"):
            errors.append("provenance.raw_result_path_external is required")

    binding = result.get("study_binding")
    if not isinstance(binding, dict):
        return StudyResultValidationResult(errors + ["study_binding must be a mapping"], warnings)

    spec_path_value = binding.get("spec_path")
    if not spec_path_value:
        return StudyResultValidationResult(errors + ["study_binding.spec_path is required"], warnings)
    spec_path = root / str(spec_path_value)
    if not spec_path.exists():
        return StudyResultValidationResult(errors + [f"missing spec: {spec_path_value}"], warnings)

    try:
        spec = _load_yaml(spec_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return StudyResultValidationResult(errors + [str(exc)], warnings)

    if spec.get("status") != "frozen":
        errors.append("bound study specification must be frozen")
    if result.get("study_id") != spec.get("study_id"):
        errors.append("result study_id does not match bound specification")

    data = spec.get("data", {})
    session_context = spec.get("session_context", {})
    operational_input = spec.get("operational_input", {})
    comparison_policy = spec.get("comparison_policy", {})

    expected_bindings = {
        "spec_status": spec.get("status"),
        "dataset_id": data.get("dataset_id"),
        "dataset_manifest": data.get("dataset_manifest"),
        "timeframe": data.get("timeframe"),
        "cutoff_utc": data.get("cutoff_utc"),
        "session_policy_id": session_context.get("policy_id"),
        "completeness_mode": session_context.get("selection", {}).get("completeness_mode"),
        "exclude_coverage_edges": session_context.get("selection", {}).get("exclude_coverage_edges"),
        "operational_rule_id": operational_input.get("rule_id"),
        "price_increment": str(operational_input.get("price_increment")),
        "statistical_significance_test": comparison_policy.get("statistical_significance_test"),
    }
    for key, expected in expected_bindings.items():
        actual = binding.get(key)
        if key == "price_increment":
            if str(actual) != str(expected):
                errors.append(f"study_binding.{key} does not match specification")
        elif actual != expected:
            errors.append(f"study_binding.{key} does not match specification")

    sample_counts = result.get("sample_counts")
    session_stats = result.get("session_statistics")
    if not isinstance(sample_counts, dict):
        errors.append("sample_counts must be a mapping")
        sample_counts = {}
    if not isinstance(session_stats, dict):
        errors.append("session_statistics must be a mapping")
        session_stats = {}

    requested_sessions = list(session_context.get("sessions") or [])
    for session_id in requested_sessions:
        count_record = sample_counts.get(session_id)
        stats_record = session_stats.get(session_id)
        if not isinstance(count_record, dict):
            errors.append(f"missing sample_counts for {session_id}")
            continue
        if not isinstance(stats_record, dict):
            errors.append(f"missing session_statistics for {session_id}")
            continue
        if int(count_record.get("selected_complete", -1)) != int(stats_record.get("n", -2)):
            errors.append(f"{session_id}: selected_complete must equal session_statistics.n")

    sample_policy = spec.get("sample_policy", {})
    primary_sessions = list(sample_policy.get("primary_sessions") or [])
    minimum_primary_n = int(sample_policy.get("minimum_primary_n", 0))
    expected_eligible = all(
        isinstance(sample_counts.get(session_id), dict)
        and int(sample_counts[session_id].get("selected_complete", 0)) >= minimum_primary_n
        for session_id in primary_sessions
    )

    primary = result.get("primary_comparison")
    if not isinstance(primary, dict):
        errors.append("primary_comparison must be a mapping")
    else:
        expected_status = "eligible" if expected_eligible else "underpowered"
        if primary.get("status") != expected_status:
            errors.append("primary_comparison.status disagrees with pre-registered sample-size gate")
        if int(primary.get("minimum_primary_n", -1)) != minimum_primary_n:
            errors.append("primary_comparison.minimum_primary_n does not match specification")

        pair = list(comparison_policy.get("primary_pair") or primary_sessions[:2])
        if len(pair) == 2:
            left, right = pair
            if primary.get("left_session") != left or primary.get("right_session") != right:
                errors.append("primary comparison pair does not match specification")
            features = list(spec.get("features") or [])
            for feature in features:
                comparison = primary.get(feature)
                if not isinstance(comparison, dict):
                    errors.append(f"primary_comparison missing feature {feature}")
                    continue

                if feature == "bars_seen":
                    left_median = session_stats.get(left, {}).get("bars_seen_median")
                    right_median = session_stats.get(right, {}).get("bars_seen_median")
                else:
                    left_feature = session_stats.get(left, {}).get(feature)
                    right_feature = session_stats.get(right, {}).get(feature)
                    left_median = left_feature.get("median") if isinstance(left_feature, dict) else None
                    right_median = right_feature.get("median") if isinstance(right_feature, dict) else None

                if left_median is None or right_median is None:
                    errors.append(f"cannot validate {feature}: missing session medians")
                    continue

                expected_difference = float(left_median) - float(right_median)
                if not _same_number(comparison.get("median_difference_left_minus_right"), expected_difference):
                    errors.append(f"{feature}: median difference is inconsistent with recorded medians")

                expected_ratio = None if float(right_median) == 0.0 else float(left_median) / float(right_median)
                actual_ratio = comparison.get("median_ratio_left_over_right")
                if expected_ratio is None:
                    if actual_ratio is not None:
                        errors.append(f"{feature}: median ratio must be null when right median is zero")
                elif not _same_number(actual_ratio, expected_ratio):
                    errors.append(f"{feature}: median ratio is inconsistent with recorded medians")

    boundaries = result.get("interpretation_boundaries")
    if not isinstance(boundaries, dict):
        errors.append("interpretation_boundaries must be a mapping")
    else:
        spec_boundaries = spec.get("interpretation_boundaries", {})
        for key in REQUIRED_INTERPRETATION_BOUNDARIES:
            if spec_boundaries.get(key) is True and boundaries.get(key) is not True:
                errors.append(f"interpretation boundary {key} must remain true")

    return StudyResultValidationResult(errors, warnings)


def validate_repository_study_results(repo_root: str | Path = ".") -> StudyResultValidationResult:
    root = Path(repo_root)
    result_dir = root / "quant" / "results"
    if not result_dir.exists():
        return StudyResultValidationResult([f"missing: {result_dir}"], [])

    paths = sorted(result_dir.glob("*.yaml"))
    if not paths:
        return StudyResultValidationResult(["no study result YAML files found"], [])

    errors: list[str] = []
    warnings: list[str] = []
    for path in paths:
        result = validate_study_result(path, root)
        errors.extend(f"{path.name}: {message}" for message in result.errors)
        warnings.extend(f"{path.name}: {message}" for message in result.warnings)
    return StudyResultValidationResult(errors, warnings)


def format_result(result: StudyResultValidationResult) -> dict[str, object]:
    return {
        "status": result.status,
        "errors": result.errors,
        "warnings": result.warnings,
    }
