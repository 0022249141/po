from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import yaml

from .signal_evaluation_validation import validate_signal_evaluation_file
from .strategy_spec_validation import validate_strategy_spec


STUDY_CLASS = "posthoc_exploratory_diagnostic"
EXPECTED_STUDY_ID = "xauusd_ny_preopen_range_compression_exploratory_v1"
EXPECTED_STRATEGY_ID = "xauusd_ny_preopen_range_breakout_baseline_v1"
EXPECTED_DATASET_ID = "xauusd_o_utc_20260904_052959"
EXPECTED_REPOSITORY_BASELINE_COMMIT = "3aa528cbbed793db214093671aac249391723336"
EXPECTED_SOURCE_BACKTEST_SHA256 = "BCDD2CC10DAA31AC64C682E376FA9357C87296792E80C6785162C2EB25046238"
EXPECTED_STRATEGY_SHA256 = "02B10FBA616A5387B245FC55845252E7BBA56D66E64B32D6E36D97413887FC60"
EXPECTED_EVALUATION_SHA256 = "4CD5F006020B53E0BB7AAF0B788DDE1225827F95D506A8FEF7AFA58E4080AA8D"
EXPECTED_M5_SHA256 = "E3050E9B46B24CFA27DF27EDD7649911998DC662BB356F1715D789F232E7FECA"
EXPECTED_STRATEGY_PATH = "quant/candidates/XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.strategy.yaml"
EXPECTED_EVALUATION_PATH = "quant/candidates/XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.evaluation.yaml"
EXPECTED_DATASET_MANIFEST = "data/manifests/XAUUSD_o_UTC_20260904_052959.json"
EXPECTED_SOURCE_BACKTEST_PATH = "MT5_UTC_EXPORTS/XAUUSD_o_20260904_052959_UTC/strategy_signal_backtest_v1.json"
EXPECTED_M5_PATH = "MT5_UTC_EXPORTS/XAUUSD_o_20260904_052959_UTC/XAUUSD_o_M5_bars_utc.csv"
EXPECTED_EVALUATION_ID = "xauusd_ny_preopen_range_breakout_baseline_v1_gross_signal_eval"

EXPECTED_BUCKET_THRESHOLDS = {
    "compressed_upper_exclusive": "1/3",
    "normal_lower_inclusive": "1/3",
    "normal_upper_exclusive": "2/3",
    "expanded_lower_inclusive": "2/3",
}
EXPECTED_BUCKET_LABELS = {
    "compressed": "percentile < 1/3",
    "normal": "1/3 <= percentile < 2/3",
    "expanded": "percentile >= 2/3",
}
EXPECTED_REPORT_METRICS = [
    "trades",
    "net_R",
    "expectancy_R",
    "profit_factor",
    "win_rate",
    "stop_rate",
    "average_R",
    "median_R",
]
EXPECTED_BREAKDOWNS = [
    "overall",
    "by_side",
    "by_compression_bucket",
    "side_x_compression_bucket",
    "regime_x_side_x_compression_bucket",
]


@dataclass(frozen=True)
class RangeCompressionStudyValidationResult:
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


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def _normalized_relative_path(value: Any) -> str:
    return Path(str(value).replace("\\", "/")).as_posix()


def _repo_path(root: Path, value: Any) -> Path:
    candidate = Path(str(value).replace("\\", "/"))
    return candidate if candidate.is_absolute() else root / candidate


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _aware_datetime(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _mapping(doc: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    value = doc.get(key)
    if not isinstance(value, dict):
        errors.append(f"{key} must be a mapping")
        return {}
    return value


def _require_exact(mapping: dict[str, Any], key: str, expected: Any, errors: list[str], prefix: str) -> None:
    if mapping.get(key) != expected:
        errors.append(f"{prefix}.{key} must equal {expected!r}")


def _validate_data_binding(data: dict[str, Any], root: Path, errors: list[str]) -> None:
    expected = {
        "market": "XAUUSD",
        "symbol": "XAUUSD_o",
        "dataset_id": EXPECTED_DATASET_ID,
        "dataset_manifest": EXPECTED_DATASET_MANIFEST,
        "timeframe": "M5",
        "input_timebase": "verified_utc",
        "cutoff_utc": "2026-09-04T05:29:59.763793Z",
        "closed_bars_only": True,
        "m5_bars_path": EXPECTED_M5_PATH,
        "m5_bars_sha256": EXPECTED_M5_SHA256,
    }
    for key, expected_value in expected.items():
        actual = data.get(key)
        if key.endswith("sha256"):
            if str(actual).upper() != expected_value:
                errors.append(f"data.{key} must equal {expected_value!r}")
        elif actual != expected_value:
            errors.append(f"data.{key} must equal {expected_value!r}")

    if _aware_datetime(data.get("cutoff_utc")) is None:
        errors.append("data.cutoff_utc must be timezone-aware ISO-8601")

    manifest_path = _repo_path(root, data.get("dataset_manifest", ""))
    if not manifest_path.is_file():
        errors.append(f"missing dataset manifest: {data.get('dataset_manifest')}")
        manifest: dict[str, Any] = {}
    else:
        try:
            manifest = _load_json(manifest_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"invalid dataset manifest: {exc}")
            manifest = {}

    if manifest:
        if manifest.get("dataset_id") != data.get("dataset_id"):
            errors.append("data.dataset_id does not match dataset manifest")
        m5_records = [
            item
            for item in manifest.get("files", [])
            if isinstance(item, dict) and item.get("timeframe") == "M5"
        ]
        if len(m5_records) != 1:
            errors.append("dataset manifest must declare exactly one M5 file")
        else:
            record = m5_records[0]
            if Path(str(data.get("m5_bars_path", ""))).name != str(record.get("path")):
                errors.append("data.m5_bars_path does not match manifest M5 file")
            if str(record.get("sha256", "")).upper() != str(data.get("m5_bars_sha256", "")).upper():
                errors.append("data.m5_bars_sha256 does not match manifest M5 file")

    m5_path = _repo_path(root, data.get("m5_bars_path", ""))
    if not m5_path.is_file():
        errors.append(f"missing bound M5 bars: {data.get('m5_bars_path')}")
    else:
        actual_hash = _sha256_file(m5_path)
        if actual_hash != str(data.get("m5_bars_sha256", "")).upper():
            errors.append("bound M5 bars SHA256 does not match data.m5_bars_sha256")


def _validate_strategy_and_evaluation(binding: dict[str, Any], root: Path, errors: list[str]) -> None:
    expected_binding = {
        "strategy_spec_id": EXPECTED_STRATEGY_ID,
        "strategy_spec_path": EXPECTED_STRATEGY_PATH,
        "strategy_spec_sha256": EXPECTED_STRATEGY_SHA256,
        "strategy_status_required": "frozen_signal_spec",
        "evaluation_id": EXPECTED_EVALUATION_ID,
        "evaluation_spec_path": EXPECTED_EVALUATION_PATH,
        "evaluation_spec_sha256": EXPECTED_EVALUATION_SHA256,
    }
    for key, expected_value in expected_binding.items():
        actual = binding.get(key)
        if key.endswith("sha256"):
            if str(actual).upper() != expected_value:
                errors.append(f"source_binding.{key} must equal {expected_value!r}")
        elif actual != expected_value:
            errors.append(f"source_binding.{key} must equal {expected_value!r}")

    strategy_path = _repo_path(root, binding.get("strategy_spec_path", ""))
    if not strategy_path.is_file():
        errors.append(f"missing bound strategy: {binding.get('strategy_spec_path')}")
    else:
        actual_hash = _sha256_file(strategy_path)
        if actual_hash != EXPECTED_STRATEGY_SHA256:
            errors.append("bound frozen strategy SHA256 does not match the frozen study binding")
        if actual_hash != str(binding.get("strategy_spec_sha256", "")).upper():
            errors.append("source_binding.strategy_spec_sha256 does not match frozen strategy file")
        validation = validate_strategy_spec(strategy_path, root)
        errors.extend(f"bound strategy: {item}" for item in validation.errors)
        try:
            strategy = _load_yaml(strategy_path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"invalid bound strategy: {exc}")
        else:
            if strategy.get("spec_id") != binding.get("strategy_spec_id"):
                errors.append("source_binding.strategy_spec_id does not match frozen strategy")
            if strategy.get("status") != binding.get("strategy_status_required"):
                errors.append("bound strategy status does not match source binding")

    evaluation_path = _repo_path(root, binding.get("evaluation_spec_path", ""))
    if not evaluation_path.is_file():
        errors.append(f"missing bound evaluation: {binding.get('evaluation_spec_path')}")
    else:
        actual_hash = _sha256_file(evaluation_path)
        if actual_hash != EXPECTED_EVALUATION_SHA256:
            errors.append("bound frozen evaluation SHA256 does not match the frozen study binding")
        if actual_hash != str(binding.get("evaluation_spec_sha256", "")).upper():
            errors.append("source_binding.evaluation_spec_sha256 does not match frozen evaluation file")
        validation = validate_signal_evaluation_file(evaluation_path, root)
        errors.extend(f"bound evaluation: {item}" for item in validation.errors)
        try:
            evaluation = _load_yaml(evaluation_path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"invalid bound evaluation: {exc}")
        else:
            if evaluation.get("evaluation_id") != binding.get("evaluation_id"):
                errors.append("source_binding.evaluation_id does not match frozen evaluation")
            if evaluation.get("bound_strategy_spec_id") != binding.get("strategy_spec_id"):
                errors.append("frozen evaluation is not bound to the frozen strategy")


def _validate_source_backtest(
    spec: dict[str, Any],
    binding: dict[str, Any],
    data: dict[str, Any],
    root: Path,
    errors: list[str],
) -> None:
    expected_binding = {
        "source_backtest_path": EXPECTED_SOURCE_BACKTEST_PATH,
        "source_backtest_class": "gross_signal_research_v1",
        "source_backtest_trade_ledger_required": True,
        "source_backtest_outcomes_are_read_only": True,
        "source_regime_is_reporting_only": True,
    }
    for key, expected_value in expected_binding.items():
        _require_exact(binding, key, expected_value, errors, "source_binding")

    if str(spec.get("source_repository_baseline_commit", "")) != EXPECTED_REPOSITORY_BASELINE_COMMIT:
        errors.append("source_repository_baseline_commit does not match the frozen repository baseline")
    if str(spec.get("source_backtest_sha256", "")).upper() != EXPECTED_SOURCE_BACKTEST_SHA256:
        errors.append("source_backtest_sha256 does not match the frozen source artifact")

    artifact_path = _repo_path(root, binding.get("source_backtest_path", ""))
    if not artifact_path.is_file():
        errors.append(f"missing bound source backtest artifact: {binding.get('source_backtest_path')}")
        return

    actual_hash = _sha256_file(artifact_path)
    if actual_hash != EXPECTED_SOURCE_BACKTEST_SHA256:
        errors.append("bound source backtest artifact SHA256 does not match frozen source_backtest_sha256")
    if actual_hash != str(spec.get("source_backtest_sha256", "")).upper():
        errors.append("source_backtest_sha256 does not match bound source backtest artifact")

    try:
        artifact = _load_json(artifact_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(f"invalid source backtest artifact: {exc}")
        return

    expected_artifact_fields = {
        "backtest_class": binding.get("source_backtest_class"),
        "strategy_spec_id": binding.get("strategy_spec_id"),
        "evaluation_id": binding.get("evaluation_id"),
        "dataset_id": data.get("dataset_id"),
        "session_policy_id": "xauusd_major_fx_sessions_v1",
    }
    for key, expected_value in expected_artifact_fields.items():
        if artifact.get(key) != expected_value:
            errors.append(f"source backtest artifact {key} does not match frozen binding")

    artifact_cutoff = _aware_datetime(artifact.get("cutoff_utc"))
    spec_cutoff = _aware_datetime(data.get("cutoff_utc"))
    if artifact_cutoff is None or spec_cutoff is None or artifact_cutoff != spec_cutoff:
        errors.append("source backtest artifact cutoff_utc does not match bound dataset cutoff")

    if _normalized_relative_path(artifact.get("input_csv", "")) != _normalized_relative_path(data.get("m5_bars_path", "")):
        errors.append("source backtest artifact input_csv does not match bound M5 bars")

    ledger = artifact.get("trade_ledger")
    if not isinstance(ledger, list) or not ledger:
        errors.append("source backtest artifact must contain a non-empty trade_ledger")
        return
    try:
        if int(artifact.get("trade_count")) != len(ledger):
            errors.append("source backtest artifact trade_count does not match trade_ledger length")
    except (TypeError, ValueError):
        errors.append("source backtest artifact trade_count must be an integer")

    required_trade_fields = {
        "session_date",
        "side",
        "entry_price",
        "exit_reason",
        "gross_R",
        "reference_high",
        "reference_low",
        "regime",
    }
    seen_dates: set[str] = set()
    for index, trade in enumerate(ledger):
        if not isinstance(trade, dict):
            errors.append(f"source backtest trade_ledger[{index}] must be a mapping")
            continue
        missing = sorted(required_trade_fields - set(trade))
        if missing:
            errors.append(f"source backtest trade_ledger[{index}] missing fields: {missing}")
            continue
        session_date = str(trade["session_date"])
        if session_date in seen_dates:
            errors.append("source backtest artifact has duplicate trade session_date values")
        seen_dates.add(session_date)
        if str(trade.get("side", "")).lower() not in {"long", "short"}:
            errors.append(f"source backtest trade_ledger[{index}] has unsupported side")
        try:
            reference_high = float(trade["reference_high"])
            reference_low = float(trade["reference_low"])
            float(trade["entry_price"])
            float(trade["gross_R"])
            if reference_high <= reference_low:
                errors.append(f"source backtest trade_ledger[{index}] has non-positive reference width")
        except (TypeError, ValueError):
            errors.append(f"source backtest trade_ledger[{index}] has non-numeric price or R fields")


def _validate_causal_features(spec: dict[str, Any], errors: list[str]) -> None:
    reference_width = _mapping(spec, "reference_width", errors)
    _require_exact(reference_width, "current_reference_width", "reference_high - reference_low", errors, "reference_width")
    _require_exact(
        reference_width,
        "source_history_includes_no_trigger_eligible_dates",
        True,
        errors,
        "reference_width",
    )
    _require_exact(
        reference_width,
        "source_history_excludes_incomplete_or_non_positive_reference_dates",
        True,
        errors,
        "reference_width",
    )

    features = _mapping(spec, "causal_features", errors)
    _require_exact(features, "lookback_eligible_reference_widths", 20, errors, "causal_features")
    baseline = _mapping(features, "lagged_baseline", errors)
    expected_baseline = {
        "statistic": "median",
        "window": "immediately_preceding_20_eligible_reference_widths",
        "current_date_in_baseline": False,
        "centered_window": False,
        "shift_direction": "lagged_only",
    }
    for key, expected_value in expected_baseline.items():
        _require_exact(baseline, key, expected_value, errors, "causal_features.lagged_baseline")

    primary = _mapping(features, "primary_feature", errors)
    _require_exact(primary, "name", "relative_range_ratio", errors, "causal_features.primary_feature")
    _require_exact(
        primary,
        "formula",
        "current_reference_width / lagged_20_reference_width_median",
        errors,
        "causal_features.primary_feature",
    )
    rank = _mapping(features, "causal_rank", errors)
    expected_rank = {
        "target": "current_reference_width",
        "comparator_window": "immediately_preceding_20_eligible_reference_widths_only",
        "percentile_method": "midrank_fraction_count_less_plus_half_equal_over_n",
    }
    for key, expected_value in expected_rank.items():
        _require_exact(rank, key, expected_value, errors, "causal_features.causal_rank")

    buckets = _mapping(features, "frozen_descriptive_buckets", errors)
    thresholds = _mapping(buckets, "thresholds", errors)
    if thresholds != EXPECTED_BUCKET_THRESHOLDS:
        errors.append("causal_features.frozen_descriptive_buckets.thresholds must exactly declare frozen thirds")
    labels = _mapping(buckets, "labels", errors)
    if labels != EXPECTED_BUCKET_LABELS:
        errors.append("causal_features.frozen_descriptive_buckets.labels must exactly declare compressed, normal, expanded")

    penetration = _mapping(spec, "breakout_penetration", errors)
    _require_exact(penetration, "long", "entry_price - reference_high", errors, "breakout_penetration")
    _require_exact(penetration, "short", "reference_low - entry_price", errors, "breakout_penetration")
    secondary = _mapping(penetration, "secondary_feature", errors)
    _require_exact(secondary, "name", "penetration_ratio", errors, "breakout_penetration.secondary_feature")
    _require_exact(
        secondary,
        "formula",
        "breakout_penetration / current_reference_width",
        errors,
        "breakout_penetration.secondary_feature",
    )

    causality = _mapping(spec, "causality_policy", errors)
    for key in (
        "current_day_leakage_prohibited",
        "current_day_in_lagged_baseline_prohibited",
        "centered_windows_prohibited",
        "negative_shifts_prohibited",
        "future_data_prohibited",
        "current_reference_width_is_complete_before_new_york_breakout_trigger",
        "source_trade_outcomes_do_not_define_features",
    ):
        _require_exact(causality, key, True, errors, "causality_policy")


def _validate_reporting_and_boundaries(spec: dict[str, Any], errors: list[str]) -> None:
    reporting = _mapping(spec, "reporting", errors)
    _require_exact(reporting, "trade_filtering_permitted", False, errors, "reporting")
    _require_exact(reporting, "retain_all_source_trades_in_annotated_ledger", True, errors, "reporting")
    _require_exact(
        reporting,
        "warmup_without_20_prior_widths",
        "retain_unassigned_in_ledger_and_overall_breakdowns",
        errors,
        "reporting",
    )
    if reporting.get("metrics") != EXPECTED_REPORT_METRICS:
        errors.append("reporting.metrics must contain the frozen required descriptive metrics in order")
    if reporting.get("breakdowns") != EXPECTED_BREAKDOWNS:
        errors.append("reporting.breakdowns must contain the frozen required breakdowns in order")
    _require_exact(reporting, "minimum_cell_size", 10, errors, "reporting")
    _require_exact(reporting, "underpowered_label", "underpowered_descriptive_only", errors, "reporting")
    _require_exact(reporting, "statistical_significance_test", "none", errors, "reporting")

    boundaries = _mapping(spec, "interpretation_boundaries", errors)
    required_true = (
        "descriptive_only",
        "statistical_significance_claim_prohibited",
        "profitability_claim_prohibited",
        "strategy_promotion_prohibited",
        "automatic_filter_generation_prohibited",
        "same_sample_findings_cannot_validate_v2",
        "source_regime_definition_not_modified",
        "gross_R_is_not_net_profitability",
    )
    for key in required_true:
        _require_exact(boundaries, key, True, errors, "interpretation_boundaries")
    _require_exact(boundaries, "live_trading_permission", False, errors, "interpretation_boundaries")

    change_control = _mapping(spec, "change_control", errors)
    for key in (
        "frozen_spec_is_immutable",
        "any_change_requires_new_version",
        "no_lookback_tuning_after_results",
        "no_bucket_threshold_tuning_after_results",
        "no_strategy_parameter_tuning_after_results",
        "no_hypothesis_rewrite_after_results",
    ):
        _require_exact(change_control, key, True, errors, "change_control")


def validate_range_compression_study_spec(
    path: str | Path,
    repo_root: str | Path = ".",
) -> RangeCompressionStudyValidationResult:
    root = Path(repo_root)
    spec_path = Path(path)
    if not spec_path.is_absolute():
        spec_path = root / spec_path
    errors: list[str] = []
    warnings: list[str] = []

    if not spec_path.is_file():
        return RangeCompressionStudyValidationResult([f"missing: {spec_path}"], warnings)
    try:
        spec = _load_yaml(spec_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return RangeCompressionStudyValidationResult([str(exc)], warnings)

    for field in (
        "version",
        "study_id",
        "study_name",
        "status",
        "study_type",
        "study_class",
        "frozen_at_utc",
        "research_question",
        "source_repository_baseline_commit",
        "source_backtest_sha256",
        "source_binding",
        "data",
        "reference_width",
        "causal_features",
        "breakout_penetration",
        "causality_policy",
        "reporting",
        "interpretation_boundaries",
        "change_control",
    ):
        if field not in spec:
            errors.append(f"missing required field: {field}")

    if spec.get("version") != 1:
        errors.append("version must be 1")
    if spec.get("study_id") != EXPECTED_STUDY_ID:
        errors.append(f"study_id must equal {EXPECTED_STUDY_ID!r}")
    if spec.get("study_name") != "XAUUSD_NY_PREOPEN_RANGE_COMPRESSION_EXPLORATORY_V1":
        errors.append("study_name must equal XAUUSD_NY_PREOPEN_RANGE_COMPRESSION_EXPLORATORY_V1")
    if spec.get("status") != "frozen":
        errors.append("status must be frozen")
    if spec.get("study_type") != STUDY_CLASS or spec.get("study_class") != STUDY_CLASS:
        errors.append(f"study_type and study_class must both equal {STUDY_CLASS!r}")
    if not str(spec.get("research_question", "")).strip():
        errors.append("research_question must be non-empty")
    if _aware_datetime(spec.get("frozen_at_utc")) is None:
        errors.append("frozen_at_utc must be timezone-aware ISO-8601")

    binding = _mapping(spec, "source_binding", errors)
    data = _mapping(spec, "data", errors)
    _validate_data_binding(data, root, errors)
    _validate_strategy_and_evaluation(binding, root, errors)
    _validate_source_backtest(spec, binding, data, root, errors)
    _validate_causal_features(spec, errors)
    _validate_reporting_and_boundaries(spec, errors)
    return RangeCompressionStudyValidationResult(errors, warnings)


def validate_repository_range_compression_study_specs(
    repo_root: str | Path = ".",
) -> RangeCompressionStudyValidationResult:
    root = Path(repo_root)
    studies_dir = root / "quant" / "studies"
    paths = sorted(studies_dir.glob("*RANGE_COMPRESSION_EXPLORATORY*.yaml"))
    if not paths:
        return RangeCompressionStudyValidationResult(["no range-compression study specifications found"], [])

    errors: list[str] = []
    warnings: list[str] = []
    for path in paths:
        result = validate_range_compression_study_spec(path, root)
        errors.extend(f"{path.name}: {message}" for message in result.errors)
        warnings.extend(f"{path.name}: {message}" for message in result.warnings)
    return RangeCompressionStudyValidationResult(errors, warnings)


def format_result(result: RangeCompressionStudyValidationResult) -> dict[str, object]:
    return {"status": result.status, "errors": result.errors, "warnings": result.warnings}
