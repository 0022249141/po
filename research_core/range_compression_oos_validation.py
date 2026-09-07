"""Strict, closed-schema validation of the prospective protocol and frozen dependencies."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import yaml

SPEC_PATH = "quant/studies/XAUUSD_NY_PREOPEN_RANGE_COMPRESSION_PROSPECTIVE_OOS_V1.yaml"
STUDY_ID = "xauusd_ny_preopen_range_compression_prospective_oos_v1"
START = "2026-09-08"
SOURCE_COMMIT = "940dc830a07bc4b168508f8cc514e2fe25936ca0"
STRATEGY_PATH = "quant/candidates/XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.strategy.yaml"
EVALUATION_PATH = "quant/candidates/XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.evaluation.yaml"
REGIME_PATH = "quant/studies/XAUUSD_NAMED_SESSION_TPO_REGIME_ROBUSTNESS_V1.yaml"
EXPLORATORY_PATH = "quant/studies/XAUUSD_NY_PREOPEN_RANGE_COMPRESSION_EXPLORATORY_V1.yaml"


def frozen_contract():
    return {
        "version": 1, "study_id": STUDY_ID,
        "study_name": "XAUUSD_NY_PREOPEN_RANGE_COMPRESSION_PROSPECTIVE_OOS_V1",
        "study_class": "prospective_oos_replication", "status": "frozen",
        "implementation_source_commit": SOURCE_COMMIT,
        "exploratory_study_id": "xauusd_ny_preopen_range_compression_exploratory_v1",
        "strategy_spec_id": "xauusd_ny_preopen_range_breakout_baseline_v1",
        "strategy_spec_sha256": "02B10FBA616A5387B245FC55845252E7BBA56D66E64B32D6E36D97413887FC60",
        "source_backtest_sha256": "BCDD2CC10DAA31AC64C682E376FA9357C87296792E80C6785162C2EB25046238",
        "dataset_id": "xauusd_o_utc_20260904_052959",
        "prospective_start_session_date": START,
        "historical_state_initialization_permitted": True,
        "historical_trade_outcomes_in_oos_metrics": False,
        "primary_hypothesis": "Future baseline V1 compressed shorts have weaker continuation than normal or expanded shorts.",
        "primary_group": {"side": "short", "compression_bucket": ["compressed"]},
        "comparator_group": {"side": "short", "compression_bucket": ["normal", "expanded"]},
        "secondary_group": {"regime": "high", "side": "short", "compression_bucket": ["compressed"]},
        "secondary_minimum_trades": 10,
        "secondary_underpowered_label": "underpowered_descriptive_only",
        "secondary_cannot_replace_primary": True,
        "compression": {
            "implementation": "research_core/range_compression_study.py",
            "lookback": 20, "window": "immediately_preceding_20_eligible_reference_widths",
            "baseline": "median", "current_session_in_baseline": False,
            "percentile": "(count(prior < current) + 0.5 * count(prior == current)) / 20",
            "thresholds": {"compressed": "p < 1/3", "normal": "1/3 <= p < 2/3", "expanded": "p >= 2/3"},
        },
        "execution": {"implementation": "research_core/strategy_signal_backtest.py",
                      "semantics": "exact_frozen_v1", "trade_suppression": False,
                      "stop_exit_reasons": ["protective_stop", "protective_stop_gap"]},
        "primary_minimum_trades": {"compressed_short": 20, "noncompressed_short": 20},
        "replication_gate": ["compressed.expectancy_R < 0", "compressed.profit_factor < 1",
                             "compressed.median_R < 0", "compressed.stop_rate > comparator.stop_rate",
                             "compressed.expectancy_R < comparator.expectancy_R"],
        "delta_expectancy_R": "compressed_short_expectancy_R - noncompressed_short_expectancy_R",
        "statuses": ["insufficient_oos_sample", "prospective_descriptive_replication", "not_replicated"],
        "interim_policy": "counts_and_data_validation_only_performance_suppressed_until_20_20",
        "metric_basis": "frozen_gross_R_zero_cost_net_R_is_sum_not_net_profitability",
        "future_data": {"timeframe": "M5", "input_timebase": "verified_utc",
                        "closed_bars_only": True, "bundle_hash_verification_required": True,
                        "cumulative_history_required": True, "old_artifact_need_not_contain_future_bars": True},
        "change_control": {key: False for key in (
            "change_start_date", "restart_oos", "rebase_oos", "drop_observations", "change_primary_group",
            "change_comparator", "change_sample_gate", "change_lookback", "change_thresholds",
            "change_entry_exit", "penetration_filters", "select_favorable_regime", "alter_v1_from_oos",
            "automatic_strategy_v2", "thresholds_from_development_effect_size")},
        "interpretation": {"descriptive_only": True, "statistical_significance_claim": False,
                           "validated_profitability_claim": False, "strategy_promotion": False},
        "live_trading_permission": False,
    }


@dataclass(frozen=True)
class OOSValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def status(self):
        return "fail" if self.errors else "pass"


def validate_range_compression_oos_spec(path=SPEC_PATH, repo_root="."):
    root=Path(repo_root); path=Path(path); path=path if path.is_absolute() else root/path; errors=[]
    try: doc=yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc: return OOSValidationResult([str(exc)],[])
    expected={"study_id":STUDY_ID,"study_name":"XAUUSD_NY_PREOPEN_RANGE_COMPRESSION_PROSPECTIVE_OOS_V1","study_class":"prospective_oos_replication","status":"frozen","implementation_source_commit":SOURCE_COMMIT,"prospective_outcome_start_session":START,"strategy_spec_sha256":"02B10FBA616A5387B245FC55845252E7BBA56D66E64B32D6E36D97413887FC60","source_backtest_sha256":"BCDD2CC10DAA31AC64C682E376FA9357C87296792E80C6785162C2EB25046238","primary_group":{"side":"short","compression_bucket":["compressed"]},"comparator_group":{"side":"short","compression_bucket":["normal","expanded"]},"minimum_oos_sample":{"compressed_short":20,"noncompressed_short":20},"live_trading_permission":False}
    for k,v in expected.items():
        if doc.get(k)!=v: errors.append(f"immutable field mismatch: {k}")
    if doc.get("historical_trade_outcomes_prohibited_from_oos_metrics") is not True: errors.append("historical outcomes must be excluded")
    if doc.get("compression",{}).get("lookback") != 20: errors.append("lookback must be 20")
    if doc.get("compression",{}).get("thresholds") != {"compressed":"p < 1/3","normal":"1/3 <= p < 2/3","expanded":"p >= 2/3"}: errors.append("bucket thresholds are immutable")
    return OOSValidationResult(errors,[])

