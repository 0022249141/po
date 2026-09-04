from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class StrategySpecValidationResult:
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


def validate_strategy_spec(path: str | Path, repo_root: str | Path = ".") -> StrategySpecValidationResult:
    root = Path(repo_root)
    spec_path = Path(path)
    if not spec_path.is_absolute():
        spec_path = root / spec_path

    errors: list[str] = []
    warnings: list[str] = []
    if not spec_path.exists():
        return StrategySpecValidationResult([f"missing: {spec_path}"], warnings)

    try:
        spec = _load_yaml(spec_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return StrategySpecValidationResult([str(exc)], warnings)

    if spec.get("status") != "frozen_signal_spec":
        errors.append("strategy status must be frozen_signal_spec")
    if spec.get("spec_class") != "rule_based_research_baseline":
        errors.append("spec_class must be rule_based_research_baseline")

    data = spec.get("data")
    if not isinstance(data, dict):
        errors.append("data must be a mapping")
        data = {}
    if data.get("dataset_id") != "xauusd_o_utc_20260904_052959":
        errors.append("dataset_id must remain bound to canonical XAUUSD UTC dataset")
    if data.get("timeframe") != "M5":
        errors.append("timeframe must remain M5")
    if data.get("input_timebase") != "verified_utc":
        errors.append("input_timebase must be verified_utc")
    if data.get("closed_bars_only") is not True or data.get("forming_bars_prohibited") is not True:
        errors.append("closed/forming-bar policy is not frozen")

    session = spec.get("session_context")
    if not isinstance(session, dict):
        errors.append("session_context must be a mapping")
        session = {}
    if session.get("policy_id") != "xauusd_major_fx_sessions_v1":
        errors.append("session policy id is not frozen")
    if session.get("primary_session") != "new_york":
        errors.append("primary session must be new_york")
    if session.get("reference_session_membership_required") != "london":
        errors.append("reference bars must remain London-classified")
    if session.get("boundaries_from_policy_only") is not True:
        errors.append("session boundaries must come only from policy")

    reference = spec.get("reference_range")
    if not isinstance(reference, dict):
        errors.append("reference_range must be a mapping")
        reference = {}
    expected_reference = {
        "duration_minutes": 240,
        "expected_m5_bars": 48,
        "all_bars_must_be_closed": True,
        "all_bars_must_be_present": True,
        "all_bars_must_classify_as_london": True,
        "high_rule": "maximum_high_of_reference_bars",
        "low_rule": "minimum_low_of_reference_bars",
    }
    for key, expected in expected_reference.items():
        if reference.get(key) != expected:
            errors.append(f"reference_range.{key} does not match frozen baseline")

    regime = spec.get("regime_context")
    if not isinstance(regime, dict):
        errors.append("regime_context must be a mapping")
        regime = {}
    if regime.get("allowed_as_reporting_dimension") is not True:
        errors.append("regime context must remain reportable")
    if regime.get("allowed_as_entry_filter") is not False:
        errors.append("regime context must not filter V1 entries")
    if regime.get("allowed_to_change_direction") is not False:
        errors.append("regime context must not change V1 direction")
    if regime.get("current_day_outcome_in_label_prohibited") is not True:
        errors.append("current-day outcome must be prohibited from regime label")

    entry = spec.get("entry")
    if not isinstance(entry, dict):
        errors.append("entry must be a mapping")
        entry = {}
    expected_entry = {
        "side_policy": "symmetric_long_short",
        "trigger_priority": "first_qualifying_closed_bar_only",
        "long_trigger": "first_closed_m5_close_strictly_above_reference_high",
        "short_trigger": "first_closed_m5_close_strictly_below_reference_low",
        "order_type": "market",
        "fill_timing": "next_m5_bar_open",
        "maximum_trades_per_session": 1,
        "opposite_signal_after_first_trigger": "ignore",
    }
    for key, expected in expected_entry.items():
        if entry.get(key) != expected:
            errors.append(f"entry.{key} does not match frozen baseline")

    stop = spec.get("invalidation_and_stop")
    if not isinstance(stop, dict):
        errors.append("invalidation_and_stop must be a mapping")
        stop = {}
    if stop.get("long_stop_level") != "reference_low":
        errors.append("long stop must remain reference_low")
    if stop.get("short_stop_level") != "reference_high":
        errors.append("short stop must remain reference_high")
    if stop.get("stop_may_not_be_widened") is not True:
        errors.append("stop widening must remain prohibited")

    exit_cfg = spec.get("exit")
    if not isinstance(exit_cfg, dict):
        errors.append("exit must be a mapping")
        exit_cfg = {}
    if exit_cfg.get("profit_target") != "none":
        errors.append("V1 baseline must not introduce a profit target")
    if exit_cfg.get("trailing_stop") != "none":
        errors.append("V1 baseline must not introduce a trailing stop")
    if exit_cfg.get("time_exit") != "new_york_session_end":
        errors.append("time exit must remain New York session end")

    execution = spec.get("execution_model")
    if not isinstance(execution, dict):
        errors.append("execution_model must be a mapping")
        execution = {}
    if execution.get("status") != "execution_cost_qualification_required_before_net_backtest_claim":
        errors.append("execution model must remain explicitly unqualified for net claims")
    if execution.get("net_profitability_claim_allowed") is not False:
        errors.append("net profitability claims must remain prohibited")
    if execution.get("promotion_to_live_allowed") is not False:
        errors.append("live promotion must remain prohibited")

    causality = spec.get("causality")
    if not isinstance(causality, dict):
        errors.append("causality must be a mapping")
        causality = {}
    required_true = (
        "future_data_prohibited",
        "same_bar_close_fill_prohibited",
        "centered_windows_prohibited",
        "negative_shift_prohibited",
        "finalized_full_new_york_session_features_as_entry_inputs_prohibited",
        "reference_range_complete_before_first_possible_trigger",
    )
    for key in required_true:
        if causality.get(key) is not True:
            errors.append(f"causality.{key} must remain true")

    params = spec.get("baseline_parameters")
    if not isinstance(params, dict):
        errors.append("baseline_parameters must be a mapping")
        params = {}
    if params.get("pre_ny_reference_minutes") != 240:
        errors.append("pre-NY reference minutes must remain 240")
    if params.get("trigger_window_minutes") != 240:
        errors.append("trigger window minutes must remain 240")
    if params.get("optimization_in_v1") != "prohibited":
        errors.append("V1 optimization must remain prohibited")

    acceptance = spec.get("acceptance_criteria_for_signal_research")
    if not isinstance(acceptance, dict):
        errors.append("acceptance criteria must be a mapping")
        acceptance = {}
    if acceptance.get("failure_action") != "reject_v1_without_parameter_tuning":
        errors.append("failure action must reject V1 without tuning")
    if acceptance.get("execution_cost_sensitivity_required_before_promotion") is not True:
        errors.append("execution-cost sensitivity must remain required before promotion")

    boundaries = spec.get("interpretation_boundaries")
    if not isinstance(boundaries, dict):
        errors.append("interpretation_boundaries must be a mapping")
        boundaries = {}
    for key in (
        "research_baseline_only",
        "not_final_strategy",
        "prior_session_range_findings_do_not_prove_this_hypothesis",
        "predictive_edge_not_established",
        "profitability_not_established",
    ):
        if boundaries.get(key) is not True:
            errors.append(f"interpretation boundary {key} must remain true")
    if boundaries.get("permission_to_trade") is not False:
        errors.append("permission_to_trade must remain false")

    return StrategySpecValidationResult(errors, warnings)


def validate_repository_strategy_specs(repo_root: str | Path = ".") -> StrategySpecValidationResult:
    root = Path(repo_root)
    paths = sorted((root / "quant" / "candidates").glob("*.strategy.yaml"))
    if not paths:
        return StrategySpecValidationResult(["no strategy specification YAML files found"], [])
    errors: list[str] = []
    warnings: list[str] = []
    for path in paths:
        result = validate_strategy_spec(path, root)
        errors.extend(f"{path.name}: {message}" for message in result.errors)
        warnings.extend(f"{path.name}: {message}" for message in result.warnings)
    return StrategySpecValidationResult(errors, warnings)


def format_result(result: StrategySpecValidationResult) -> dict[str, object]:
    return {"status": result.status, "errors": result.errors, "warnings": result.warnings}
