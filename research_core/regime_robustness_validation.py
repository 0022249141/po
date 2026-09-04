from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .study_spec_validation import validate_study_spec
from .temporal_result_validation import validate_temporal_result


@dataclass(frozen=True)
class RegimeRobustnessValidationResult:
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


def _same(left: Any, right: Any) -> bool:
    return left == right


def validate_regime_robustness_spec(
    path: str | Path,
    repo_root: str | Path = ".",
) -> RegimeRobustnessValidationResult:
    root = Path(repo_root)
    spec_path = Path(path)
    if not spec_path.is_absolute():
        spec_path = root / spec_path

    base = validate_study_spec(spec_path, root)
    errors = list(base.errors)
    warnings = list(base.warnings)
    if errors:
        return RegimeRobustnessValidationResult(errors, warnings)

    try:
        spec = _load_yaml(spec_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return RegimeRobustnessValidationResult([str(exc)], warnings)

    follow = spec.get("follow_up_design")
    regime = spec.get("regime_robustness")
    if not isinstance(follow, dict):
        errors.append("follow_up_design must be a mapping")
        follow = {}
    if not isinstance(regime, dict):
        errors.append("regime_robustness must be a mapping")
        regime = {}

    if follow.get("follow_up_after_temporal_result") is not True:
        errors.append("follow_up_design.follow_up_after_temporal_result must be true")

    base_spec_rel = follow.get("base_spec_path")
    base_result_rel = follow.get("base_result_path")
    temporal_spec: dict[str, Any] = {}
    if not base_spec_rel:
        errors.append("follow_up_design.base_spec_path is required")
    else:
        base_spec_path = root / str(base_spec_rel)
        if not base_spec_path.exists():
            errors.append(f"missing temporal base spec: {base_spec_rel}")
        else:
            try:
                temporal_spec = _load_yaml(base_spec_path)
                if temporal_spec.get("status") != "frozen":
                    errors.append("temporal base specification must be frozen")
                if follow.get("base_study_id") != temporal_spec.get("study_id"):
                    errors.append("follow_up_design.base_study_id does not match temporal base spec")
            except (OSError, ValueError, yaml.YAMLError) as exc:
                errors.append(str(exc))

    if not base_result_rel:
        errors.append("follow_up_design.base_result_path is required")
    else:
        result_validation = validate_temporal_result(root / str(base_result_rel), root)
        errors.extend(f"temporal base result: {message}" for message in result_validation.errors)

    # Freeze the research/data layer to the completed temporal study. Only conditioning is new.
    if temporal_spec:
        for key in ("data", "session_context", "operational_input", "features"):
            if not _same(spec.get(key), temporal_spec.get(key)):
                errors.append(f"{key} must match temporal base specification exactly")
        current_pair = spec.get("comparison_policy", {}).get("primary_pair")
        base_pair = temporal_spec.get("comparison_policy", {}).get("primary_pair")
        if current_pair != base_pair:
            errors.append("comparison_policy.primary_pair must match temporal base specification")

    reference = follow.get("base_observed_direction_reference")
    if not isinstance(reference, dict) or not reference:
        errors.append("follow_up_design.base_observed_direction_reference must be a non-empty mapping")
        reference = {}

    expected_fixed = {
        "regime_id": "lagged_paired_range_rank_v1",
        "regime_class": "project_defined_causal_lagged_range_conditioning",
        "canonical_market_regime_claim": False,
        "pairing_key": "session_instance_local_date",
        "pair_requirement": "both_primary_sessions_complete",
        "composite_feature": "range_ticks",
        "composite_formula": "arithmetic_mean_of_london_and_new_york_range_ticks_on_each_prior_paired_date",
        "current_date_label_uses_only_prior_paired_dates": True,
        "lookback_paired_dates": 20,
        "warmup_minimum_paired_dates": 20,
        "rank_target": "most_recent_prior_paired_date_composite",
        "rank_window": "previous_20_paired_dates",
        "percentile_method": "midrank_fraction_count_less_plus_half_equal_over_n",
        "eligible_regime_rule": "both primary sessions meet minimum_pair_n_per_regime",
        "statistical_significance_test": "none",
    }
    for key, expected in expected_fixed.items():
        if regime.get(key) != expected:
            errors.append(f"regime_robustness.{key} must equal {expected!r}")

    thresholds = regime.get("thresholds")
    expected_thresholds = {
        "low_upper_exclusive": "1/3",
        "normal_lower_inclusive": "1/3",
        "normal_upper_exclusive": "2/3",
        "high_lower_inclusive": "2/3",
    }
    if thresholds != expected_thresholds:
        errors.append("regime_robustness.thresholds do not match frozen thirds")

    if regime.get("labels") != ["low", "normal", "high"]:
        errors.append("regime_robustness.labels must be [low, normal, high]")

    try:
        minimum = int(regime.get("minimum_pair_n_per_regime"))
        if minimum < 2:
            errors.append("regime_robustness.minimum_pair_n_per_regime must be >= 2")
    except (TypeError, ValueError):
        errors.append("regime_robustness.minimum_pair_n_per_regime must be an integer")

    features = set(spec.get("features") or [])
    directional = regime.get("directional_features")
    if not isinstance(directional, list) or not directional:
        errors.append("regime_robustness.directional_features must be a non-empty list")
        directional = []
    unknown = [feature for feature in directional if feature not in features]
    if unknown:
        errors.append(f"directional features are not in study features: {unknown}")
    missing_reference = [feature for feature in directional if feature not in reference]
    if missing_reference:
        errors.append(f"missing base direction references: {missing_reference}")

    allowed_direction_values = {"london_gt_new_york", "new_york_gt_london", "tie"}
    invalid_reference = {
        feature: reference.get(feature)
        for feature in directional
        if reference.get(feature) not in allowed_direction_values
    }
    if invalid_reference:
        errors.append(f"unsupported base direction references: {invalid_reference}")

    if spec.get("causality_policy", {}).get("current_date_outcome_in_regime_label_prohibited") is not True:
        errors.append("causality_policy.current_date_outcome_in_regime_label_prohibited must be true")

    return RegimeRobustnessValidationResult(errors, warnings)


def validate_repository_regime_robustness_specs(
    repo_root: str | Path = ".",
) -> RegimeRobustnessValidationResult:
    root = Path(repo_root)
    study_dir = root / "quant" / "studies"
    paths = sorted(study_dir.glob("*REGIME_ROBUSTNESS*.yaml"))
    if not paths:
        return RegimeRobustnessValidationResult(["no regime robustness specifications found"], [])

    errors: list[str] = []
    warnings: list[str] = []
    for path in paths:
        result = validate_regime_robustness_spec(path, root)
        errors.extend(f"{path.name}: {message}" for message in result.errors)
        warnings.extend(f"{path.name}: {message}" for message in result.warnings)
    return RegimeRobustnessValidationResult(errors, warnings)


def format_result(result: RegimeRobustnessValidationResult) -> dict[str, object]:
    return {"status": result.status, "errors": result.errors, "warnings": result.warnings}
