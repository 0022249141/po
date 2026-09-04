from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class SignalResultValidationResult:
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


def validate_signal_result(path: str | Path, repo_root: str | Path = ".") -> SignalResultValidationResult:
    root = Path(repo_root)
    result_path = Path(path)
    if not result_path.is_absolute():
        result_path = root / result_path
    errors: list[str] = []
    warnings: list[str] = []

    if not result_path.exists():
        return SignalResultValidationResult([f"missing: {result_path}"], warnings)
    try:
        result = _load_yaml(result_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return SignalResultValidationResult([str(exc)], warnings)

    if result.get("status") != "recorded":
        errors.append("result status must be recorded")
    if result.get("result_type") != "compact_gross_signal_result":
        errors.append("result_type must be compact_gross_signal_result")

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
        return SignalResultValidationResult(errors + ["binding must be a mapping"], warnings)

    strategy_path = root / str(binding.get("strategy_spec_path", ""))
    evaluation_path = root / str(binding.get("evaluation_spec_path", ""))
    if not strategy_path.exists():
        errors.append("bound strategy specification is missing")
        strategy = {}
    else:
        strategy = _load_yaml(strategy_path)
    if not evaluation_path.exists():
        errors.append("bound evaluation specification is missing")
        evaluation = {}
    else:
        evaluation = _load_yaml(evaluation_path)

    if result.get("strategy_spec_id") != strategy.get("spec_id"):
        errors.append("strategy_spec_id does not match bound strategy")
    if result.get("evaluation_id") != evaluation.get("evaluation_id"):
        errors.append("evaluation_id does not match bound evaluation")
    if binding.get("dataset_id") != strategy.get("data", {}).get("dataset_id"):
        errors.append("binding.dataset_id does not match strategy")
    if binding.get("timeframe") != strategy.get("data", {}).get("timeframe"):
        errors.append("binding.timeframe does not match strategy")
    if binding.get("cutoff_utc") != strategy.get("data", {}).get("cutoff_utc"):
        errors.append("binding.cutoff_utc does not match strategy")
    if binding.get("session_policy_id") != strategy.get("session_context", {}).get("policy_id"):
        errors.append("binding.session_policy_id does not match strategy")
    if binding.get("cost_model") != evaluation.get("cost_model", {}).get("class"):
        errors.append("binding.cost_model does not match evaluation")
    if binding.get("backtest_class") != "gross_signal_research_v1":
        errors.append("binding.backtest_class must be gross_signal_research_v1")

    sample = result.get("sample")
    if not isinstance(sample, dict):
        errors.append("sample must be a mapping")
        sample = {}
    try:
        total = int(sample.get("trade_count"))
        long_n = int(sample.get("long_trades"))
        short_n = int(sample.get("short_trades"))
        if total != long_n + short_n:
            errors.append("trade_count must equal long_trades + short_trades")
        eligible_months = int(sample.get("eligible_months"))
        positive_months = int(sample.get("positive_months"))
        if positive_months > eligible_months:
            errors.append("positive_months cannot exceed eligible_months")
    except (TypeError, ValueError):
        errors.append("sample counts must be integers")

    metrics = result.get("metrics")
    if not isinstance(metrics, dict):
        errors.append("metrics must be a mapping")
        metrics = {}
    for key in ("gross_expectancy_R", "gross_profit_factor", "max_drawdown_R"):
        try:
            float(metrics.get(key))
        except (TypeError, ValueError):
            errors.append(f"metrics.{key} must be numeric")

    acceptance = result.get("acceptance")
    if not isinstance(acceptance, dict):
        errors.append("acceptance must be a mapping")
        acceptance = {}
    checks = acceptance.get("checks") if isinstance(acceptance, dict) else None
    required_checks = (
        "minimum_total_trades",
        "minimum_long_trades",
        "minimum_short_trades",
        "gross_expectancy_R_positive",
        "gross_profit_factor_above_one",
        "minimum_positive_months",
    )
    if not isinstance(checks, dict):
        errors.append("acceptance.checks must be a mapping")
        checks = {}
    for key in required_checks:
        if checks.get(key) is not True:
            errors.append(f"acceptance check {key} must be true for recorded pass")
    if acceptance.get("passed") is not all(checks.get(key) is True for key in required_checks):
        errors.append("acceptance.passed is inconsistent with checks")

    criteria = strategy.get("acceptance_criteria_for_signal_research", {})
    try:
        if int(sample.get("trade_count", -1)) < int(criteria.get("minimum_total_trades", 10**9)):
            errors.append("recorded trade_count does not satisfy frozen minimum")
        if int(sample.get("long_trades", -1)) < int(criteria.get("minimum_long_trades", 10**9)):
            errors.append("recorded long_trades does not satisfy frozen minimum")
        if int(sample.get("short_trades", -1)) < int(criteria.get("minimum_short_trades", 10**9)):
            errors.append("recorded short_trades does not satisfy frozen minimum")
        if float(metrics.get("gross_expectancy_R", -1e99)) <= float(criteria.get("gross_expectancy_R_must_be_greater_than", 0.0)):
            errors.append("recorded gross expectancy does not satisfy frozen minimum")
        if float(metrics.get("gross_profit_factor", -1e99)) <= float(criteria.get("gross_profit_factor_must_be_greater_than", 1.0)):
            errors.append("recorded gross profit factor does not satisfy frozen minimum")
        if int(sample.get("positive_months", -1)) < int(criteria.get("minimum_positive_months_out_of_eligible_months", 10**9)):
            errors.append("recorded positive months do not satisfy frozen minimum")
    except (TypeError, ValueError):
        errors.append("unable to evaluate frozen acceptance criteria")

    boundaries = result.get("interpretation_boundaries")
    required_true = (
        "gross_zero_cost_only",
        "net_profitability_not_tested",
        "execution_costs_unresolved",
        "predictive_edge_not_promoted",
        "live_trading_prohibited",
        "parameter_tuning_after_result_prohibited",
    )
    if not isinstance(boundaries, dict):
        errors.append("interpretation_boundaries must be a mapping")
    else:
        for key in required_true:
            if boundaries.get(key) is not True:
                errors.append(f"interpretation boundary {key} must remain true")

    return SignalResultValidationResult(errors, warnings)


def validate_repository_signal_results(repo_root: str | Path = ".") -> SignalResultValidationResult:
    root = Path(repo_root)
    paths = sorted((root / "quant" / "results").glob("*.gross.result.yaml"))
    if not paths:
        return SignalResultValidationResult(["no gross signal result YAML files found"], [])
    errors: list[str] = []
    warnings: list[str] = []
    for path in paths:
        result = validate_signal_result(path, root)
        errors.extend(f"{path.name}: {message}" for message in result.errors)
        warnings.extend(f"{path.name}: {message}" for message in result.warnings)
    return SignalResultValidationResult(errors, warnings)


def format_result(result: SignalResultValidationResult) -> dict[str, object]:
    return {"status": result.status, "errors": result.errors, "warnings": result.warnings}
