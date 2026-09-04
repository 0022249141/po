from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REQUIRED_LABELS = ("low", "normal", "high")
REQUIRED_FEATURES = ("range_ticks", "occupancy_events")
REQUIRED_BOUNDARIES = (
    "descriptive_only",
    "trading_signal_prohibited",
    "profitability_claim_prohibited",
    "statistical_significance_not_tested",
    "causal_regime_labeling_only",
    "regime_definition_is_project_defined",
    "predictive_edge_not_established",
)


@dataclass(frozen=True)
class RegimeResultValidationResult:
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


def validate_regime_result(path: str | Path, repo_root: str | Path = ".") -> RegimeResultValidationResult:
    root = Path(repo_root)
    result_path = Path(path)
    if not result_path.is_absolute():
        result_path = root / result_path
    errors: list[str] = []
    warnings: list[str] = []

    if not result_path.exists():
        return RegimeResultValidationResult([f"missing: {result_path}"], warnings)
    try:
        result = _load_yaml(result_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return RegimeResultValidationResult([str(exc)], warnings)

    if result.get("status") != "recorded":
        errors.append("result status must be recorded")
    if result.get("result_type") != "compact_regime_robustness_result":
        errors.append("result_type must be compact_regime_robustness_result")

    provenance = result.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance must be a mapping")
    else:
        if provenance.get("raw_result_committed") is not False:
            errors.append("raw_result_committed must be false")
        for key in ("execution_command", "summary_command", "raw_result_path_external"):
            if not provenance.get(key):
                errors.append(f"provenance.{key} is required")

    binding = result.get("study_binding")
    if not isinstance(binding, dict):
        return RegimeResultValidationResult(errors + ["study_binding must be a mapping"], warnings)
    spec_rel = binding.get("spec_path")
    if not spec_rel:
        return RegimeResultValidationResult(errors + ["study_binding.spec_path is required"], warnings)
    spec_path = root / str(spec_rel)
    if not spec_path.exists():
        return RegimeResultValidationResult(errors + [f"missing spec: {spec_rel}"], warnings)
    try:
        spec = _load_yaml(spec_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return RegimeResultValidationResult(errors + [str(exc)], warnings)

    if spec.get("status") != "frozen":
        errors.append("bound regime specification must be frozen")
    if result.get("study_id") != spec.get("study_id"):
        errors.append("result study_id does not match specification")

    data = spec.get("data", {})
    session = spec.get("session_context", {})
    selection = session.get("selection", {}) if isinstance(session, dict) else {}
    op = spec.get("operational_input", {})
    follow = spec.get("follow_up_design", {})
    regime = spec.get("regime_robustness", {})
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
        "regime_id": regime.get("regime_id"),
        "lookback_paired_dates": regime.get("lookback_paired_dates"),
        "minimum_pair_n_per_regime": regime.get("minimum_pair_n_per_regime"),
        "statistical_significance_test": regime.get("statistical_significance_test"),
    }
    for key, expected in expected_bindings.items():
        actual = binding.get(key)
        if key == "price_increment":
            if str(actual) != str(expected):
                errors.append(f"study_binding.{key} does not match specification")
        elif actual != expected:
            errors.append(f"study_binding.{key} does not match specification")

    accounting = result.get("sample_accounting")
    if not isinstance(accounting, dict):
        errors.append("sample_accounting must be a mapping")
        accounting = {}
    try:
        paired = int(accounting.get("paired_date_count"))
        warmup = int(accounting.get("warmup_excluded_paired_dates"))
        labeled = int(accounting.get("labeled_paired_date_count"))
        if paired - warmup != labeled:
            errors.append("paired_date_count - warmup_excluded_paired_dates must equal labeled_paired_date_count")
        if warmup != int(regime.get("lookback_paired_dates", -1)):
            errors.append("warmup_excluded_paired_dates must equal frozen lookback")
    except (TypeError, ValueError):
        errors.append("sample accounting counts must be integers")

    buckets = result.get("regime_buckets")
    if not isinstance(buckets, dict):
        errors.append("regime_buckets must be a mapping")
        buckets = {}
    eligible_labels: list[str] = []
    total_labeled_from_buckets = 0
    minimum_n = int(regime.get("minimum_pair_n_per_regime", 0))
    reference = follow.get("base_observed_direction_reference", {})
    for label in REQUIRED_LABELS:
        record = buckets.get(label)
        if not isinstance(record, dict):
            errors.append(f"missing regime bucket: {label}")
            continue
        try:
            london_n = int(record.get("london_n"))
            new_york_n = int(record.get("new_york_n"))
            if london_n != new_york_n:
                errors.append(f"{label}: paired London/New York counts must match")
            total_labeled_from_buckets += min(london_n, new_york_n)
            expected_eligible = london_n >= minimum_n and new_york_n >= minimum_n
            if bool(record.get("eligible")) != expected_eligible:
                errors.append(f"{label}: eligible flag disagrees with minimum-pair-n rule")
            if expected_eligible:
                eligible_labels.append(label)
        except (TypeError, ValueError):
            errors.append(f"{label}: counts must be integers")
        for feature in REQUIRED_FEATURES:
            actual_direction = record.get(f"{feature}_direction")
            if actual_direction not in {"new_york_gt_london", "london_gt_new_york", "tie"}:
                errors.append(f"{label}: invalid {feature} direction")

    if accounting:
        try:
            if total_labeled_from_buckets != int(accounting.get("labeled_paired_date_count")):
                errors.append("regime bucket counts do not sum to labeled_paired_date_count")
            recorded_eligible = list(accounting.get("eligible_regimes") or [])
            if recorded_eligible != eligible_labels:
                errors.append("sample_accounting.eligible_regimes is inconsistent")
            if int(accounting.get("eligible_regime_count", -1)) != len(eligible_labels):
                errors.append("sample_accounting.eligible_regime_count is inconsistent")
        except (TypeError, ValueError):
            errors.append("sample_accounting eligibility count must be an integer")

    persistence = result.get("directional_persistence")
    if not isinstance(persistence, dict):
        errors.append("directional_persistence must be a mapping")
    else:
        for feature in REQUIRED_FEATURES:
            record = persistence.get(feature)
            if not isinstance(record, dict):
                errors.append(f"missing directional persistence: {feature}")
                continue
            expected_base = reference.get(feature)
            if record.get("base_direction") != expected_base:
                errors.append(f"{feature}: base_direction does not match frozen reference")
            matches = sum(
                1
                for label in eligible_labels
                if isinstance(buckets.get(label), dict)
                and buckets[label].get(f"{feature}_direction") == expected_base
            )
            if int(record.get("eligible_regime_count", -1)) != len(eligible_labels):
                errors.append(f"{feature}: eligible_regime_count is inconsistent")
            if int(record.get("matching_direction_regime_count", -1)) != matches:
                errors.append(f"{feature}: matching_direction_regime_count is inconsistent")
            expected_fraction = matches / len(eligible_labels) if eligible_labels else None
            actual_fraction = record.get("matching_direction_fraction")
            if expected_fraction is None:
                if actual_fraction is not None:
                    errors.append(f"{feature}: matching_direction_fraction must be null")
            else:
                try:
                    if abs(float(actual_fraction) - expected_fraction) > 1e-12:
                        errors.append(f"{feature}: matching_direction_fraction is inconsistent")
                except (TypeError, ValueError):
                    errors.append(f"{feature}: matching_direction_fraction must be numeric")

    boundaries = result.get("interpretation_boundaries")
    if not isinstance(boundaries, dict):
        errors.append("interpretation_boundaries must be a mapping")
    else:
        for key in REQUIRED_BOUNDARIES:
            if boundaries.get(key) is not True:
                errors.append(f"interpretation boundary {key} must remain true")

    return RegimeResultValidationResult(errors, warnings)


def validate_repository_regime_results(repo_root: str | Path = ".") -> RegimeResultValidationResult:
    root = Path(repo_root)
    result_dir = root / "quant" / "results"
    paths = sorted(result_dir.glob("*REGIME_ROBUSTNESS*.result.yaml"))
    if not paths:
        return RegimeResultValidationResult(["no regime robustness result YAML files found"], [])
    errors: list[str] = []
    warnings: list[str] = []
    for path in paths:
        result = validate_regime_result(path, root)
        errors.extend(f"{path.name}: {message}" for message in result.errors)
        warnings.extend(f"{path.name}: {message}" for message in result.warnings)
    return RegimeResultValidationResult(errors, warnings)


def format_result(result: RegimeResultValidationResult) -> dict[str, object]:
    return {"status": result.status, "errors": result.errors, "warnings": result.warnings}
