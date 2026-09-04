from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .study_result_validation import validate_study_result
from .study_spec_validation import validate_study_spec


@dataclass(frozen=True)
class TemporalRobustnessValidationResult:
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


def validate_temporal_robustness_spec(
    path: str | Path,
    repo_root: str | Path = ".",
) -> TemporalRobustnessValidationResult:
    root = Path(repo_root)
    spec_path = Path(path)
    if not spec_path.is_absolute():
        spec_path = root / spec_path

    base_validation = validate_study_spec(spec_path, root)
    errors = list(base_validation.errors)
    warnings = list(base_validation.warnings)
    if errors:
        return TemporalRobustnessValidationResult(errors, warnings)

    try:
        spec = _load_yaml(spec_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return TemporalRobustnessValidationResult([str(exc)], warnings)

    follow_up = spec.get("follow_up_design")
    temporal = spec.get("temporal_robustness")
    if not isinstance(follow_up, dict):
        errors.append("follow_up_design must be a mapping")
        follow_up = {}
    if not isinstance(temporal, dict):
        errors.append("temporal_robustness must be a mapping")
        temporal = {}

    if follow_up.get("follow_up_after_base_result") is not True:
        errors.append("follow_up_design.follow_up_after_base_result must be true")

    base_spec_rel = follow_up.get("base_spec_path")
    base_result_rel = follow_up.get("base_result_path")
    if not base_spec_rel:
        errors.append("follow_up_design.base_spec_path is required")
    else:
        base_spec_path = root / str(base_spec_rel)
        if not base_spec_path.exists():
            errors.append(f"missing base spec: {base_spec_rel}")
        else:
            try:
                base_spec = _load_yaml(base_spec_path)
                if base_spec.get("status") != "frozen":
                    errors.append("base study specification must be frozen")
                if follow_up.get("base_study_id") != base_spec.get("study_id"):
                    errors.append("follow_up_design.base_study_id does not match base spec")
            except (OSError, ValueError, yaml.YAMLError) as exc:
                errors.append(str(exc))

    if not base_result_rel:
        errors.append("follow_up_design.base_result_path is required")
    else:
        result_validation = validate_study_result(root / str(base_result_rel), root)
        errors.extend(f"base result: {message}" for message in result_validation.errors)

    reference = follow_up.get("base_observed_direction_reference")
    if not isinstance(reference, dict) or not reference:
        errors.append("follow_up_design.base_observed_direction_reference must be a non-empty mapping")
        reference = {}

    if temporal.get("bucket_basis") != "session_local_start_month":
        errors.append("temporal_robustness.bucket_basis must be session_local_start_month")
    if temporal.get("bucket_key_source") != "session_instance_id":
        errors.append("temporal_robustness.bucket_key_source must be session_instance_id")
    if temporal.get("bucket_format") != "YYYY-MM":
        errors.append("temporal_robustness.bucket_format must be YYYY-MM")
    try:
        minimum = int(temporal.get("minimum_pair_n_per_bucket"))
        if minimum < 2:
            errors.append("temporal_robustness.minimum_pair_n_per_bucket must be >= 2")
    except (TypeError, ValueError):
        errors.append("temporal_robustness.minimum_pair_n_per_bucket must be an integer")

    features = set(spec.get("features") or [])
    directional = temporal.get("directional_features")
    if not isinstance(directional, list) or not directional:
        errors.append("temporal_robustness.directional_features must be a non-empty list")
        directional = []
    unknown_directional = [feature for feature in directional if feature not in features]
    if unknown_directional:
        errors.append(f"directional features are not in study features: {unknown_directional}")
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

    if temporal.get("eligible_bucket_rule") != "both primary sessions meet minimum_pair_n_per_bucket":
        errors.append("temporal_robustness.eligible_bucket_rule is not frozen to the project rule")
    if temporal.get("statistical_significance_test") not in (None, "none"):
        errors.append("temporal robustness significance test must be none")
    if temporal.get("regime_labels") not in (None, "none"):
        errors.append("temporal robustness V1 must not introduce regime labels")

    return TemporalRobustnessValidationResult(errors, warnings)


def validate_repository_temporal_robustness_specs(
    repo_root: str | Path = ".",
) -> TemporalRobustnessValidationResult:
    root = Path(repo_root)
    study_dir = root / "quant" / "studies"
    paths = sorted(study_dir.glob("*TEMPORAL_ROBUSTNESS*.yaml"))
    if not paths:
        return TemporalRobustnessValidationResult(["no temporal robustness specifications found"], [])

    errors: list[str] = []
    warnings: list[str] = []
    for path in paths:
        result = validate_temporal_robustness_spec(path, root)
        errors.extend(f"{path.name}: {message}" for message in result.errors)
        warnings.extend(f"{path.name}: {message}" for message in result.warnings)
    return TemporalRobustnessValidationResult(errors, warnings)


def format_result(result: TemporalRobustnessValidationResult) -> dict[str, object]:
    return {"status": result.status, "errors": result.errors, "warnings": result.warnings}
