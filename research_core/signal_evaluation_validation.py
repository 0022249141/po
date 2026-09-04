from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class SignalEvaluationValidationResult:
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


def validate_signal_evaluation_document(doc: dict[str, Any], repo_root: str | Path = ".") -> SignalEvaluationValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    root = Path(repo_root)

    required = (
        "version",
        "evaluation_id",
        "status",
        "bound_strategy_spec",
        "bound_strategy_spec_id",
        "data",
        "fills",
        "cost_model",
        "returns",
        "reporting",
        "acceptance_binding",
        "interpretation_boundaries",
    )
    for field in required:
        if field not in doc:
            errors.append(f"missing required field: {field}")

    if doc.get("status") != "frozen":
        errors.append("status must be frozen")

    strategy_path = root / str(doc.get("bound_strategy_spec", ""))
    if not strategy_path.is_file():
        errors.append(f"bound strategy spec not found: {strategy_path}")
    else:
        try:
            strategy = _load_yaml(strategy_path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"unable to load bound strategy spec: {exc}")
        else:
            if strategy.get("spec_id") != doc.get("bound_strategy_spec_id"):
                errors.append("bound_strategy_spec_id does not match strategy spec")
            if strategy.get("status") != "frozen_signal_spec":
                errors.append("bound strategy spec must be frozen_signal_spec")

    data = doc.get("data")
    if not isinstance(data, dict):
        errors.append("data must be a mapping")
    else:
        if data.get("timeframe") != "M5":
            errors.append("data.timeframe must be M5")
        for key in (
            "verified_utc_required",
            "closed_bars_only",
            "complete_reference_range_required",
            "complete_new_york_session_required_for_evaluation",
        ):
            if data.get(key) is not True:
                errors.append(f"data.{key} must be true")
        if int(data.get("expected_new_york_m5_bars", 0)) != 108:
            errors.append("data.expected_new_york_m5_bars must be 108")

    fills = doc.get("fills")
    if not isinstance(fills, dict):
        errors.append("fills must be a mapping")
    else:
        exact = {
            "entry_fill": "next_m5_bar_open_after_trigger",
            "stop_gap_rule": "bar_open_if_open_beyond_stop_otherwise_stop_level",
            "time_exit_rule": "final_closed_m5_bar_close_of_new_york_session",
            "time_exit_timestamp": "new_york_session_end",
        }
        for key, expected in exact.items():
            if fills.get(key) != expected:
                errors.append(f"fills.{key} must be {expected}")
        if fills.get("same_trigger_bar_fill_prohibited") is not True:
            errors.append("fills.same_trigger_bar_fill_prohibited must be true")
        if fills.get("protective_stop_active_on_entry_bar") is not True:
            errors.append("fills.protective_stop_active_on_entry_bar must be true")
        if fills.get("stop_touch_rule") != "inclusive":
            errors.append("fills.stop_touch_rule must be inclusive")

    cost = doc.get("cost_model")
    if not isinstance(cost, dict):
        errors.append("cost_model must be a mapping")
    else:
        if cost.get("class") != "gross_zero_cost_signal_evaluation":
            errors.append("cost_model.class must be gross_zero_cost_signal_evaluation")
        for key in ("commission_applied", "slippage_applied", "spread_applied", "net_profitability_claim_allowed"):
            if cost.get(key) is not False:
                errors.append(f"cost_model.{key} must be false")

    returns = doc.get("returns")
    if not isinstance(returns, dict) or returns.get("unit") != "R":
        errors.append("returns.unit must be R")

    reporting = doc.get("reporting")
    if not isinstance(reporting, dict):
        errors.append("reporting must be a mapping")
    else:
        for key in (
            "trade_ledger_required",
            "overall_metrics_required",
            "long_short_split_required",
            "calendar_month_split_required",
            "regime_split_required",
            "regime_is_reporting_only",
            "regime_filtering_prohibited",
        ):
            if reporting.get(key) is not True:
                errors.append(f"reporting.{key} must be true")
        if reporting.get("eligible_month_definition") != "at_least_one_evaluated_trade":
            errors.append("reporting.eligible_month_definition must be at_least_one_evaluated_trade")

    acceptance = doc.get("acceptance_binding")
    if not isinstance(acceptance, dict):
        errors.append("acceptance_binding must be a mapping")
    else:
        if acceptance.get("no_parameter_tuning_after_result") is not True:
            errors.append("acceptance_binding.no_parameter_tuning_after_result must be true")
        if acceptance.get("failure_action") != "reject_v1_without_parameter_tuning":
            errors.append("acceptance_binding.failure_action must be reject_v1_without_parameter_tuning")

    boundaries = doc.get("interpretation_boundaries")
    if not isinstance(boundaries, dict):
        errors.append("interpretation_boundaries must be a mapping")
    else:
        for key in (
            "signal_research_only",
            "not_net_backtest",
            "not_live_execution_model",
            "not_permission_to_trade",
            "broker_cost_qualification_still_required",
        ):
            if boundaries.get(key) is not True:
                errors.append(f"interpretation_boundaries.{key} must be true")

    return SignalEvaluationValidationResult(errors, warnings)


def validate_signal_evaluation_file(path: str | Path, repo_root: str | Path = ".") -> SignalEvaluationValidationResult:
    try:
        doc = _load_yaml(Path(path))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return SignalEvaluationValidationResult([str(exc)], [])
    return validate_signal_evaluation_document(doc, repo_root)


def format_validation_result(result: SignalEvaluationValidationResult) -> dict[str, object]:
    return {"status": result.status, "errors": result.errors, "warnings": result.warnings}
