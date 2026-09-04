from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ResidualFrictionBudgetValidationResult:
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


def validate_residual_friction_budget_spec(path: str | Path, repo_root: str | Path = ".") -> ResidualFrictionBudgetValidationResult:
    root = Path(repo_root)
    spec_path = Path(path)
    if not spec_path.is_absolute():
        spec_path = root / spec_path
    errors: list[str] = []
    warnings: list[str] = []

    if not spec_path.exists():
        return ResidualFrictionBudgetValidationResult([f"missing: {spec_path}"], warnings)
    try:
        spec = _load_yaml(spec_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return ResidualFrictionBudgetValidationResult([str(exc)], warnings)

    if spec.get("status") != "frozen":
        errors.append("status must be frozen")
    if spec.get("budget_class") != "post_spread_uniform_extra_round_trip_price_budget":
        errors.append("unexpected budget_class")

    binding = spec.get("binding")
    if not isinstance(binding, dict):
        return ResidualFrictionBudgetValidationResult(errors + ["binding must be a mapping"], warnings)
    for key in (
        "strategy_spec_path",
        "evaluation_spec_path",
        "gross_result_path",
        "spread_spec_path",
        "spread_result_path",
    ):
        rel = binding.get(key)
        if not rel or not (root / str(rel)).exists():
            errors.append(f"binding.{key} must reference an existing file")
    if binding.get("dataset_id") != "xauusd_o_utc_20260904_052959":
        errors.append("dataset_id must remain canonical")
    if binding.get("symbol") != "XAUUSD_o":
        errors.append("symbol must remain XAUUSD_o")
    try:
        if float(binding.get("point_size")) != 0.01:
            errors.append("point_size must remain 0.01")
        if float(binding.get("primary_spread_points")) != 22.0:
            errors.append("primary_spread_points must remain 22")
    except (TypeError, ValueError):
        errors.append("point_size and primary_spread_points must be numeric")
    if binding.get("primary_spread_scenario") != "observed_median_fixed":
        errors.append("primary spread scenario must remain observed_median_fixed")

    spread_result_path = root / str(binding.get("spread_result_path", ""))
    if spread_result_path.exists():
        try:
            spread_result = _load_yaml(spread_result_path)
            primary = spread_result.get("primary_gate", {}).get("scenario_id")
            if primary != binding.get("primary_spread_scenario"):
                errors.append("budget primary spread scenario must match recorded spread result")
            recorded_points = spread_result.get("scenarios", {}).get(primary, {}).get("spread_points")
            if float(recorded_points) != float(binding.get("primary_spread_points")):
                errors.append("budget primary spread points must match recorded spread result")
        except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
            errors.append(str(exc))

    method = spec.get("method")
    if not isinstance(method, dict):
        errors.append("method must be a mapping")
    else:
        expected = {
            "input_required": "full_external_gross_trade_ledger",
            "base_adjusted_R": "gross_R_minus_primary_spread_price_divided_by_initial_risk",
            "extra_cost_R_per_trade": "x_divided_by_initial_risk",
            "adjusted_R_with_extra_friction": "base_adjusted_R_minus_x_divided_by_initial_risk",
            "break_even_extra_price_formula": "sum_base_adjusted_R_divided_by_sum_inverse_initial_risk",
            "break_even_extra_points_formula": "break_even_extra_price_divided_by_point_size",
            "strict_positive_edge_condition": "extra_round_trip_price_friction_less_than_break_even_extra_price",
        }
        for key, value in expected.items():
            if method.get(key) != value:
                errors.append(f"method.{key} does not match frozen method")

    execution = spec.get("execution_path")
    if not isinstance(execution, dict):
        errors.append("execution_path must be a mapping")
    else:
        for key in (
            "signal_path_recomputed",
            "bid_ask_stop_path_recomputed",
            "commission_measured",
            "slippage_measured",
            "historical_full_sample_spread_calibrated",
        ):
            if execution.get(key) is not False:
                errors.append(f"execution_path.{key} must remain false")

    boundaries = spec.get("interpretation_boundaries")
    if not isinstance(boundaries, dict):
        errors.append("interpretation_boundaries must be a mapping")
    else:
        for key in (
            "diagnostic_budget_only",
            "no_cost_scenario_tuning",
            "no_signal_rule_changes",
            "not_measured_commission",
            "not_measured_slippage",
            "not_full_execution_path_backtest",
            "net_profitability_not_established",
            "live_trading_prohibited",
        ):
            if boundaries.get(key) is not True:
                errors.append(f"interpretation boundary {key} must remain true")

    return ResidualFrictionBudgetValidationResult(errors, warnings)


def validate_repository_residual_friction_budget(repo_root: str | Path = ".") -> ResidualFrictionBudgetValidationResult:
    root = Path(repo_root)
    paths = sorted((root / "quant" / "candidates").glob("*.residual_friction_budget.yaml"))
    if not paths:
        return ResidualFrictionBudgetValidationResult(["no residual friction budget specifications found"], [])
    errors: list[str] = []
    warnings: list[str] = []
    for path in paths:
        result = validate_residual_friction_budget_spec(path, root)
        errors.extend(f"{path.name}: {message}" for message in result.errors)
        warnings.extend(f"{path.name}: {message}" for message in result.warnings)
    return ResidualFrictionBudgetValidationResult(errors, warnings)


def format_result(result: ResidualFrictionBudgetValidationResult) -> dict[str, object]:
    return {"status": result.status, "errors": result.errors, "warnings": result.warnings}
