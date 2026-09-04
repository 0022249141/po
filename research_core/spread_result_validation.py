from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REQUIRED_BOUNDARIES = (
    "fixed_spread_sensitivity_only",
    "historical_full_sample_spread_not_calibrated",
    "not_full_bid_ask_execution_backtest",
    "commission_unresolved",
    "slippage_unresolved",
    "net_profitability_not_established",
    "live_trading_prohibited",
    "signal_rule_changes_prohibited",
)


@dataclass(frozen=True)
class SpreadResultValidationResult:
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


def _numeric(value: Any, label: str, errors: list[str]) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        errors.append(f"{label} must be numeric")
        return None


def validate_spread_result(path: str | Path, repo_root: str | Path = ".") -> SpreadResultValidationResult:
    root = Path(repo_root)
    result_path = Path(path)
    if not result_path.is_absolute():
        result_path = root / result_path
    errors: list[str] = []
    warnings: list[str] = []

    if not result_path.exists():
        return SpreadResultValidationResult([f"missing: {result_path}"], warnings)
    try:
        result = _load_yaml(result_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return SpreadResultValidationResult([str(exc)], warnings)

    if result.get("status") != "recorded":
        errors.append("result status must be recorded")
    if result.get("result_type") != "compact_spread_sensitivity_result":
        errors.append("result_type must be compact_spread_sensitivity_result")

    provenance = result.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("provenance must be a mapping")
    else:
        if provenance.get("raw_result_committed") is not False:
            errors.append("raw_result_committed must be false")
        for key in ("execution_command", "raw_result_path_external"):
            if not provenance.get(key):
                errors.append(f"provenance.{key} is required")

    binding = result.get("binding")
    if not isinstance(binding, dict):
        return SpreadResultValidationResult(errors + ["binding must be a mapping"], warnings)

    spec_rel = binding.get("sensitivity_spec_path")
    gross_rel = binding.get("gross_result_path")
    if not spec_rel or not (root / str(spec_rel)).exists():
        return SpreadResultValidationResult(errors + ["binding.sensitivity_spec_path must exist"], warnings)
    if not gross_rel or not (root / str(gross_rel)).exists():
        errors.append("binding.gross_result_path must exist")

    try:
        spec = _load_yaml(root / str(spec_rel))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return SpreadResultValidationResult(errors + [str(exc)], warnings)

    if spec.get("status") != "frozen":
        errors.append("bound spread sensitivity specification must be frozen")
    if result.get("sensitivity_id") != spec.get("sensitivity_id"):
        errors.append("result sensitivity_id does not match specification")
    if result.get("strategy_spec_id") != "xauusd_ny_preopen_range_breakout_baseline_v1":
        errors.append("strategy_spec_id mismatch")
    if binding.get("dataset_id") != spec.get("binding", {}).get("dataset_id"):
        errors.append("binding.dataset_id does not match specification")
    if str(binding.get("symbol")) != str(spec.get("binding", {}).get("symbol")):
        errors.append("binding.symbol does not match specification")
    if _numeric(binding.get("point_size"), "binding.point_size", errors) != float(spec.get("binding", {}).get("point_size")):
        errors.append("binding.point_size does not match specification")

    try:
        gross = _load_yaml(root / str(gross_rel)) if gross_rel and (root / str(gross_rel)).exists() else {}
    except (OSError, ValueError, yaml.YAMLError) as exc:
        errors.append(str(exc))
        gross = {}
    if gross:
        expected_trades = int(gross.get("sample", {}).get("trade_count", -1))
        try:
            if int(binding.get("trade_count", -2)) != expected_trades:
                errors.append("binding.trade_count does not match recorded gross result")
        except (TypeError, ValueError):
            errors.append("binding.trade_count must be an integer")

    expected_scenarios: dict[str, tuple[float, str]] = {}
    for row in spec.get("scenarios", []):
        if isinstance(row, dict):
            expected_scenarios[str(row.get("id"))] = (float(row.get("spread_points")), str(row.get("role")))

    scenarios = result.get("scenarios")
    if not isinstance(scenarios, dict):
        errors.append("scenarios must be a mapping")
        scenarios = {}
    if set(scenarios) != set(expected_scenarios):
        errors.append("result scenarios must exactly match frozen scenario ids")

    for scenario_id, (expected_points, _role) in expected_scenarios.items():
        record = scenarios.get(scenario_id)
        if not isinstance(record, dict):
            errors.append(f"missing scenario result: {scenario_id}")
            continue
        points = _numeric(record.get("spread_points"), f"{scenario_id}.spread_points", errors)
        if points is not None and abs(points - expected_points) > 1e-12:
            errors.append(f"{scenario_id}.spread_points does not match frozen specification")
        for key in ("expectancy_R", "profit_factor", "max_drawdown_R"):
            _numeric(record.get(key), f"{scenario_id}.{key}", errors)
        for key in ("positive_months", "eligible_months"):
            try:
                value = int(record.get(key))
                if value < 0:
                    errors.append(f"{scenario_id}.{key} must be non-negative")
            except (TypeError, ValueError):
                errors.append(f"{scenario_id}.{key} must be an integer")

    gate = result.get("primary_gate")
    spec_gate = spec.get("pre_frozen_gate", {})
    if not isinstance(gate, dict):
        errors.append("primary_gate must be a mapping")
    else:
        primary_id = str(spec_gate.get("primary_scenario"))
        if gate.get("scenario_id") != primary_id:
            errors.append("primary_gate.scenario_id does not match frozen specification")
        primary = scenarios.get(primary_id, {}) if isinstance(scenarios, dict) else {}
        expectancy = _numeric(primary.get("expectancy_R"), "primary expectancy_R", errors) if isinstance(primary, dict) else None
        pf = _numeric(primary.get("profit_factor"), "primary profit_factor", errors) if isinstance(primary, dict) else None
        expected_checks = {
            "expectancy_R_positive": expectancy is not None and expectancy > float(spec_gate.get("expectancy_R_must_be_greater_than", 0.0)),
            "profit_factor_above_one": pf is not None and pf > float(spec_gate.get("profit_factor_must_be_greater_than", 1.0)),
        }
        checks = gate.get("checks")
        if checks != expected_checks:
            errors.append("primary_gate.checks are inconsistent with recorded primary metrics")
        if bool(gate.get("passed")) != all(expected_checks.values()):
            errors.append("primary_gate.passed is inconsistent with recorded primary metrics")
        if gate.get("failure_action_if_failed") != spec_gate.get("failure_action"):
            errors.append("primary_gate failure action does not match frozen specification")

    boundaries = result.get("interpretation_boundaries")
    if not isinstance(boundaries, dict):
        errors.append("interpretation_boundaries must be a mapping")
    else:
        for key in REQUIRED_BOUNDARIES:
            if boundaries.get(key) is not True:
                errors.append(f"interpretation boundary {key} must remain true")

    return SpreadResultValidationResult(errors, warnings)


def validate_repository_spread_results(repo_root: str | Path = ".") -> SpreadResultValidationResult:
    root = Path(repo_root)
    paths = sorted((root / "quant" / "results").glob("*.spread.result.yaml"))
    if not paths:
        return SpreadResultValidationResult(["no spread sensitivity result YAML files found"], [])
    errors: list[str] = []
    warnings: list[str] = []
    for path in paths:
        result = validate_spread_result(path, root)
        errors.extend(f"{path.name}: {message}" for message in result.errors)
        warnings.extend(f"{path.name}: {message}" for message in result.warnings)
    return SpreadResultValidationResult(errors, warnings)


def format_result(result: SpreadResultValidationResult) -> dict[str, object]:
    return {"status": result.status, "errors": result.errors, "warnings": result.warnings}
