from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
import json

import yaml


ALLOWED_STATUSES = {"draft", "frozen", "superseded"}
ALLOWED_STUDY_TYPES = {"descriptive"}
ALLOWED_FEATURES = {
    "range_ticks",
    "occupied_bins",
    "occupancy_events",
    "mean_bin_occupancy",
    "bars_seen",
}
ALLOWED_SUMMARIES = {"n", "min", "q25", "median", "q75", "max", "mean"}
REQUIRED_TRUE_BOUNDARIES = {
    "descriptive_only",
    "trading_signal_prohibited",
    "profitability_claim_prohibited",
    "poc_value_area_prohibited",
    "ict_kill_zone_substitution_prohibited",
    "centralized_volume_claim_prohibited",
    "dealer_inventory_claim_prohibited",
}
REQUIRED_TRUE_CAUSALITY = {
    "forming_bars_prohibited",
    "future_data_prohibited",
    "session_boundary_inference_prohibited",
    "missing_data_boundary_shift_prohibited",
}


@dataclass(frozen=True)
class StudySpecValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def status(self) -> str:
        return "pass" if not self.errors else "fail"


def _yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _aware_iso(value: Any, field: str, errors: list[str]) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        errors.append(f"{field} must be ISO-8601")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{field} must be timezone-aware")
        return None
    return parsed


def validate_study_spec(path: str | Path, repo_root: str | Path = ".") -> StudySpecValidationResult:
    root = Path(repo_root)
    spec_path = Path(path)
    if not spec_path.is_absolute():
        spec_path = root / spec_path
    errors: list[str] = []
    warnings: list[str] = []

    if not spec_path.exists():
        return StudySpecValidationResult([f"missing: {spec_path}"], warnings)

    try:
        doc = _yaml(spec_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return StudySpecValidationResult([str(exc)], warnings)

    for field in (
        "version",
        "study_id",
        "status",
        "study_type",
        "research_question",
        "data",
        "session_context",
        "operational_input",
        "features",
        "summary_statistics",
        "sample_policy",
        "comparison_policy",
        "causality_policy",
        "interpretation_boundaries",
        "change_control",
    ):
        if field not in doc:
            errors.append(f"missing required field: {field}")

    if doc.get("status") not in ALLOWED_STATUSES:
        errors.append(f"unsupported status: {doc.get('status')!r}")
    if doc.get("study_type") not in ALLOWED_STUDY_TYPES:
        errors.append(f"unsupported study_type: {doc.get('study_type')!r}")
    if not str(doc.get("research_question", "")).strip():
        errors.append("research_question must be non-empty")

    if doc.get("status") == "frozen":
        _aware_iso(doc.get("frozen_at_utc"), "frozen_at_utc", errors)

    data = doc.get("data") if isinstance(doc.get("data"), dict) else {}
    if data.get("input_timebase") != "verified_utc":
        errors.append("data.input_timebase must be verified_utc")
    if data.get("closed_bars_only") is not True:
        errors.append("data.closed_bars_only must be true")
    _aware_iso(data.get("cutoff_utc"), "data.cutoff_utc", errors)

    manifest_rel = data.get("dataset_manifest")
    if not manifest_rel:
        errors.append("data.dataset_manifest is required")
        manifest = {}
    else:
        manifest_path = root / str(manifest_rel)
        if not manifest_path.exists():
            errors.append(f"missing dataset manifest: {manifest_rel}")
            manifest = {}
        else:
            try:
                manifest = _json(manifest_path)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                errors.append(str(exc))
                manifest = {}

    if manifest:
        if data.get("dataset_id") != manifest.get("dataset_id"):
            errors.append("data.dataset_id does not match dataset manifest")
        if data.get("symbol") != manifest.get("symbol"):
            errors.append("data.symbol does not match dataset manifest")
        tf = str(data.get("timeframe", ""))
        manifest_tfs = {
            str(item.get("timeframe"))
            for item in manifest.get("files", [])
            if isinstance(item, dict) and item.get("timeframe")
        }
        if tf not in manifest_tfs:
            errors.append(f"data.timeframe {tf!r} is not present in dataset manifest")

    session = doc.get("session_context") if isinstance(doc.get("session_context"), dict) else {}
    selection = session.get("selection") if isinstance(session.get("selection"), dict) else {}
    if selection.get("completeness_mode") != "complete_only":
        errors.append("session_context.selection.completeness_mode must be complete_only for this frozen study class")
    if selection.get("exclude_coverage_edges") is not True:
        errors.append("session_context.selection.exclude_coverage_edges must be true")

    policy_rel = session.get("policy_path")
    policy_doc: dict[str, Any] = {}
    if not policy_rel:
        errors.append("session_context.policy_path is required")
    else:
        policy_path = root / str(policy_rel)
        if not policy_path.exists():
            errors.append(f"missing session policy: {policy_rel}")
        else:
            try:
                policy_doc = _yaml(policy_path)
            except (OSError, ValueError, yaml.YAMLError) as exc:
                errors.append(str(exc))
    if policy_doc:
        if session.get("policy_id") != policy_doc.get("policy_id"):
            errors.append("session_context.policy_id does not match policy document")
        known_sessions = set((policy_doc.get("sessions") or {}).keys())
        requested = session.get("sessions")
        if not isinstance(requested, list) or not requested:
            errors.append("session_context.sessions must be a non-empty list")
        else:
            unknown = [item for item in requested if item not in known_sessions]
            if unknown:
                errors.append(f"unknown session ids: {unknown}")

    op = doc.get("operational_input") if isinstance(doc.get("operational_input"), dict) else {}
    rule_rel = op.get("rule_path")
    rule_doc: dict[str, Any] = {}
    if not rule_rel:
        errors.append("operational_input.rule_path is required")
    else:
        rule_path = root / str(rule_rel)
        if not rule_path.exists():
            errors.append(f"missing operational rule: {rule_rel}")
        else:
            try:
                rule_doc = _yaml(rule_path)
            except (OSError, ValueError, yaml.YAMLError) as exc:
                errors.append(str(exc))
    if rule_doc and op.get("rule_id") != rule_doc.get("operational_rule_id"):
        errors.append("operational_input.rule_id does not match operational rule document")

    try:
        increment = Decimal(str(op.get("price_increment")))
        if increment <= 0:
            raise InvalidOperation
    except (InvalidOperation, TypeError, ValueError):
        errors.append("operational_input.price_increment must be positive")
        increment = None

    if manifest and increment is not None:
        tick_size = manifest.get("symbol_metadata", {}).get("trade_tick_size")
        if tick_size is not None and increment != Decimal(str(tick_size)):
            errors.append("operational_input.price_increment must match manifest trade_tick_size")

    features = doc.get("features")
    if not isinstance(features, list) or not features:
        errors.append("features must be a non-empty list")
    else:
        unsupported = [item for item in features if item not in ALLOWED_FEATURES]
        if unsupported:
            errors.append(f"unsupported features: {unsupported}")
        if len(set(features)) != len(features):
            errors.append("features must not contain duplicates")

    summaries = doc.get("summary_statistics")
    if not isinstance(summaries, list) or not summaries:
        errors.append("summary_statistics must be a non-empty list")
    else:
        unsupported = [item for item in summaries if item not in ALLOWED_SUMMARIES]
        if unsupported:
            errors.append(f"unsupported summary statistics: {unsupported}")

    sample = doc.get("sample_policy") if isinstance(doc.get("sample_policy"), dict) else {}
    primary = sample.get("primary_sessions")
    secondary = sample.get("secondary_descriptive_sessions")
    if not isinstance(primary, list) or len(primary) < 2:
        errors.append("sample_policy.primary_sessions must contain at least two sessions")
    if not isinstance(secondary, list):
        errors.append("sample_policy.secondary_descriptive_sessions must be a list")
    try:
        if int(sample.get("minimum_primary_n")) < 2:
            errors.append("sample_policy.minimum_primary_n must be >= 2")
    except (TypeError, ValueError):
        errors.append("sample_policy.minimum_primary_n must be an integer")
    if sample.get("underpowered_action") != "descriptive_only":
        errors.append("sample_policy.underpowered_action must be descriptive_only")

    causality = doc.get("causality_policy") if isinstance(doc.get("causality_policy"), dict) else {}
    for key in REQUIRED_TRUE_CAUSALITY:
        if causality.get(key) is not True:
            errors.append(f"causality_policy.{key} must be true")

    boundaries = doc.get("interpretation_boundaries") if isinstance(doc.get("interpretation_boundaries"), dict) else {}
    for key in REQUIRED_TRUE_BOUNDARIES:
        if boundaries.get(key) is not True:
            errors.append(f"interpretation_boundaries.{key} must be true")

    change = doc.get("change_control") if isinstance(doc.get("change_control"), dict) else {}
    if doc.get("status") == "frozen":
        if change.get("frozen_spec_is_immutable") is not True:
            errors.append("frozen study requires frozen_spec_is_immutable=true")
        if change.get("any_rule_change_requires_new_version") is not True:
            errors.append("frozen study requires any_rule_change_requires_new_version=true")

    comparison = doc.get("comparison_policy") if isinstance(doc.get("comparison_policy"), dict) else {}
    if comparison.get("no_parameter_tuning_after_results") is not True:
        errors.append("comparison_policy.no_parameter_tuning_after_results must be true")
    if comparison.get("no_hypothesis_rewrite_after_results") is not True:
        errors.append("comparison_policy.no_hypothesis_rewrite_after_results must be true")
    if comparison.get("statistical_significance_test") not in (None, "none"):
        warnings.append("this descriptive study should not be interpreted as inferential significance testing")

    return StudySpecValidationResult(errors, warnings)


def validate_repository_study_specs(repo_root: str | Path = ".") -> StudySpecValidationResult:
    root = Path(repo_root)
    studies_dir = root / "quant" / "studies"
    if not studies_dir.exists():
        return StudySpecValidationResult([f"missing: {studies_dir}"], [])
    files = sorted(studies_dir.glob("*.yaml"))
    if not files:
        return StudySpecValidationResult(["no study specifications found"], [])

    errors: list[str] = []
    warnings: list[str] = []
    for path in files:
        result = validate_study_spec(path, root)
        errors.extend(f"{path.name}: {item}" for item in result.errors)
        warnings.extend(f"{path.name}: {item}" for item in result.warnings)
    return StudySpecValidationResult(errors, warnings)


def format_result(result: StudySpecValidationResult) -> dict[str, object]:
    return {"status": result.status, "errors": result.errors, "warnings": result.warnings}
