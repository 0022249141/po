from __future__ import annotations

import json
from pathlib import Path
from statistics import median
from typing import Any, Mapping

import yaml

from .metrics import summarize_pnls
from .residual_friction_budget_validation import validate_residual_friction_budget_spec


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _risk_summary(values: list[float]) -> dict[str, float]:
    if not values:
        raise ValueError("initial risk list is empty")
    ordered = sorted(values)
    return {
        "min": ordered[0],
        "median": median(ordered),
        "max": ordered[-1],
        "mean": sum(ordered) / len(ordered),
    }


def compute_residual_friction_budget(
    ledger: list[Mapping[str, Any]],
    *,
    spread_price: float,
    spread_points: float,
    point_size: float,
) -> dict[str, Any]:
    if not ledger:
        raise ValueError("trade ledger must be non-empty")
    if point_size <= 0:
        raise ValueError("point_size must be positive")
    if spread_price < 0 or spread_points < 0:
        raise ValueError("spread inputs must be non-negative")

    risks: list[float] = []
    base_adjusted: list[float] = []
    inverse_risk_sum = 0.0
    for trade in ledger:
        risk = float(trade["initial_risk"])
        gross_R = float(trade["gross_R"])
        if risk <= 0:
            raise ValueError("initial_risk must be positive for every trade")
        risks.append(risk)
        inverse_risk_sum += 1.0 / risk
        base_adjusted.append(gross_R - spread_price / risk)

    if inverse_risk_sum <= 0:
        raise ValueError("sum of inverse initial risk must be positive")

    base_metrics = summarize_pnls(base_adjusted, initial_capital=0.0)
    base_total_R = float(base_metrics["net_profit"])
    break_even_extra_price = base_total_R / inverse_risk_sum
    break_even_extra_points = break_even_extra_price / point_size
    total_break_even_round_trip_points = spread_points + break_even_extra_points
    return {
        "base_metrics": base_metrics,
        "risk_geometry": {
            "initial_risk": _risk_summary(risks),
            "sum_inverse_initial_risk": inverse_risk_sum,
        },
        "break_even_extra_round_trip_price": break_even_extra_price,
        "break_even_extra_round_trip_points": break_even_extra_points,
        "total_break_even_round_trip_points": total_break_even_round_trip_points,
    }


def run_residual_friction_budget(
    gross_result_json: str | Path,
    *,
    spec_path: str | Path = "quant/candidates/XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.residual_friction_budget.yaml",
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    root = Path(repo_root)
    budget_path = Path(spec_path)
    if not budget_path.is_absolute():
        budget_path = root / budget_path
    validation = validate_residual_friction_budget_spec(budget_path, root)
    if validation.errors:
        raise ValueError("invalid residual friction budget specification: " + "; ".join(validation.errors))
    spec = _load_yaml(budget_path)

    gross_path = Path(gross_result_json)
    gross = _load_json(gross_path)
    if gross.get("backtest_class") != "gross_signal_research_v1":
        raise ValueError("input JSON must be gross_signal_research_v1")
    if gross.get("strategy_spec_id") != "xauusd_ny_preopen_range_breakout_baseline_v1":
        raise ValueError("gross result strategy_spec_id mismatch")
    ledger = gross.get("trade_ledger")
    if not isinstance(ledger, list) or not ledger:
        raise ValueError("gross result trade_ledger must be a non-empty list")

    binding = spec["binding"]
    point_size = float(binding["point_size"])
    spread_points = float(binding["primary_spread_points"])
    spread_price = spread_points * point_size
    computed = compute_residual_friction_budget(
        ledger,
        spread_price=spread_price,
        spread_points=spread_points,
        point_size=point_size,
    )
    base_metrics = computed["base_metrics"]

    recorded_spread_path = root / str(binding["spread_result_path"])
    recorded_spread = _load_yaml(recorded_spread_path)
    primary_id = str(binding["primary_spread_scenario"])
    recorded_primary = recorded_spread.get("scenarios", {}).get(primary_id, {})
    recorded_expectancy = float(recorded_primary["expectancy_R"])
    recorded_pf = float(recorded_primary["profit_factor"])
    calculated_expectancy = float(base_metrics["expectancy"])
    calculated_pf = float(base_metrics["profit_factor"])
    if abs(calculated_expectancy - recorded_expectancy) > 1e-12:
        raise ValueError("recomputed primary spread expectancy does not match recorded spread result")
    if abs(calculated_pf - recorded_pf) > 1e-12:
        raise ValueError("recomputed primary spread profit factor does not match recorded spread result")

    return {
        "budget_class": spec["budget_class"],
        "budget_id": spec["budget_id"],
        "strategy_spec_id": gross["strategy_spec_id"],
        "gross_result_json": str(gross_path),
        "trade_count": len(ledger),
        "base_primary_spread": {
            "scenario_id": primary_id,
            "spread_points": spread_points,
            "spread_price": spread_price,
            "metrics": base_metrics,
        },
        "risk_geometry": computed["risk_geometry"],
        "residual_friction_budget": {
            "break_even_extra_round_trip_price": computed["break_even_extra_round_trip_price"],
            "break_even_extra_round_trip_points": computed["break_even_extra_round_trip_points"],
            "total_break_even_round_trip_points_including_primary_spread": computed["total_break_even_round_trip_points"],
            "strict_positive_condition": "actual_uniform_extra_round_trip_price_friction_must_be_less_than_break_even",
            "pf_and_expectancy_share_same_break_even_under_this_additive_model": True,
        },
        "interpretation_boundaries": spec["interpretation_boundaries"],
    }
