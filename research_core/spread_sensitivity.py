from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

from .metrics import summarize_pnls
from .spread_sensitivity_validation import validate_spread_sensitivity_spec


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _summarize_adjusted(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: str(row["entry_ts_utc"]))
    overall = summarize_pnls([float(row["adjusted_R"]) for row in ordered], initial_capital=0.0)
    by_side: dict[str, Any] = {}
    for side in ("long", "short"):
        vals = [float(row["adjusted_R"]) for row in ordered if row.get("side") == side]
        by_side[side] = summarize_pnls(vals, initial_capital=0.0)

    months: dict[str, list[float]] = defaultdict(list)
    for row in ordered:
        months[str(row["session_date"])[:7]].append(float(row["adjusted_R"]))
    by_month = {month: summarize_pnls(values, initial_capital=0.0) for month, values in sorted(months.items())}
    positive_months = sum(1 for metrics in by_month.values() if float(metrics["net_profit"]) > 0)
    return {
        "overall": overall,
        "by_side": by_side,
        "by_month": by_month,
        "eligible_month_count": len(by_month),
        "positive_month_count": positive_months,
    }


def run_spread_sensitivity(
    gross_result_json: str | Path,
    *,
    spec_path: str | Path = "quant/candidates/XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.spread_sensitivity.yaml",
    repo_root: str | Path = ".",
    include_adjusted_ledger: bool = False,
) -> dict[str, Any]:
    root = Path(repo_root)
    sensitivity_path = Path(spec_path)
    if not sensitivity_path.is_absolute():
        sensitivity_path = root / sensitivity_path
    validation = validate_spread_sensitivity_spec(sensitivity_path, root)
    if validation.errors:
        raise ValueError("invalid spread sensitivity specification: " + "; ".join(validation.errors))
    spec = _load_yaml(sensitivity_path)

    gross_path = Path(gross_result_json)
    gross = _load_json(gross_path)
    if gross.get("backtest_class") != "gross_signal_research_v1":
        raise ValueError("input JSON must be gross_signal_research_v1")
    if gross.get("strategy_spec_id") != "xauusd_ny_preopen_range_breakout_baseline_v1":
        raise ValueError("gross result strategy_spec_id mismatch")
    ledger = gross.get("trade_ledger")
    if not isinstance(ledger, list) or not ledger:
        raise ValueError("gross result trade_ledger must be a non-empty list")

    point_size = float(spec["binding"]["point_size"])
    scenario_results: dict[str, Any] = {}
    for scenario in spec["scenarios"]:
        scenario_id = str(scenario["id"])
        spread_points = float(scenario["spread_points"])
        spread_price = spread_points * point_size
        adjusted_rows: list[dict[str, Any]] = []
        for trade in ledger:
            initial_risk = float(trade["initial_risk"])
            if initial_risk <= 0:
                raise ValueError("initial_risk must be positive for every trade")
            gross_R = float(trade["gross_R"])
            cost_R = spread_price / initial_risk
            adjusted_rows.append(
                {
                    "session_date": str(trade["session_date"]),
                    "side": str(trade["side"]),
                    "entry_ts_utc": str(trade["entry_ts_utc"]),
                    "gross_R": gross_R,
                    "spread_cost_R": cost_R,
                    "adjusted_R": gross_R - cost_R,
                }
            )
        summary = _summarize_adjusted(adjusted_rows)
        record: dict[str, Any] = {
            "spread_points": spread_points,
            "spread_price": spread_price,
            "role": scenario["role"],
            "metrics": summary,
        }
        if include_adjusted_ledger:
            record["adjusted_ledger"] = adjusted_rows
        scenario_results[scenario_id] = record

    primary_id = str(spec["pre_frozen_gate"]["primary_scenario"])
    primary = scenario_results[primary_id]["metrics"]["overall"]
    pf = primary.get("profit_factor")
    checks = {
        "expectancy_R_positive": primary.get("expectancy") is not None
        and float(primary["expectancy"]) > float(spec["pre_frozen_gate"]["expectancy_R_must_be_greater_than"]),
        "profit_factor_above_one": pf is not None
        and float(pf) > float(spec["pre_frozen_gate"]["profit_factor_must_be_greater_than"]),
    }

    return {
        "sensitivity_class": spec["sensitivity_class"],
        "sensitivity_id": spec["sensitivity_id"],
        "strategy_spec_id": gross["strategy_spec_id"],
        "gross_result_json": str(gross_path),
        "trade_count": len(ledger),
        "scenario_results": scenario_results,
        "primary_gate": {
            "scenario_id": primary_id,
            "checks": checks,
            "passed": all(checks.values()),
            "failure_action": spec["pre_frozen_gate"]["failure_action"],
        },
        "interpretation_boundaries": spec["interpretation_boundaries"],
    }
