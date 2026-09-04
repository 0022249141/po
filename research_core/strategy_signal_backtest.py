from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

from .data_validation import TIMEFRAME_SECONDS, _norm_row, read_csv_rows
from .metrics import summarize_pnls
from .named_session_dataset import _extract_row_utc
from .regime_robustness import run_named_session_tpo_regime_robustness
from .session_policy import NamedSessionPolicy
from .signal_evaluation_validation import validate_signal_evaluation_file
from .strategy_spec_validation import validate_strategy_spec


UTC = timezone.utc


@dataclass(frozen=True)
class Bar:
    ts: datetime
    open: float
    high: float
    low: float
    close: float


@dataclass(frozen=True)
class Trade:
    session_date: str
    side: str
    trigger_close_ts: datetime
    entry_ts: datetime
    entry_price: float
    stop_price: float
    exit_ts: datetime
    exit_price: float
    exit_reason: str
    initial_risk: float
    gross_R: float
    reference_high: float
    reference_low: float
    regime: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_date": self.session_date,
            "side": self.side,
            "trigger_close_ts_utc": self.trigger_close_ts.isoformat(),
            "entry_ts_utc": self.entry_ts.isoformat(),
            "entry_price": self.entry_price,
            "stop_price": self.stop_price,
            "exit_ts_utc": self.exit_ts.isoformat(),
            "exit_price": self.exit_price,
            "exit_reason": self.exit_reason,
            "initial_risk": self.initial_risk,
            "gross_R": self.gross_R,
            "reference_high": self.reference_high,
            "reference_low": self.reference_low,
            "regime": self.regime,
        }


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _price(row: dict[str, Any], field: str) -> float:
    normalized = _norm_row(row)
    value = normalized.get(field)
    if value is None or str(value).strip() == "":
        raise ValueError(f"missing {field}")
    return float(str(value).replace(",", "").strip())


def _load_closed_bars(csv_path: str | Path, cutoff_utc: datetime, timeframe: str = "M5") -> tuple[list[Bar], dict[str, Any]]:
    tf = timeframe.upper()
    if tf not in TIMEFRAME_SECONDS:
        raise ValueError(f"unsupported timeframe: {timeframe}")
    interval = timedelta(seconds=TIMEFRAME_SECONDS[tf])
    rows, meta = read_csv_rows(csv_path)
    result: list[Bar] = []
    previous: datetime | None = None
    for raw in rows:
        ts = _extract_row_utc(raw)
        if previous is not None and ts <= previous:
            raise ValueError("input timestamps must be strictly increasing")
        previous = ts
        if ts + interval > cutoff_utc:
            continue
        bar = Bar(ts=ts, open=_price(raw, "open"), high=_price(raw, "high"), low=_price(raw, "low"), close=_price(raw, "close"))
        if bar.high < max(bar.open, bar.close) or bar.low > min(bar.open, bar.close) or bar.high < bar.low:
            raise ValueError(f"invalid OHLC at {ts.isoformat()}")
        result.append(bar)
    return result, meta


def _expected_opens(start: datetime, end: datetime, interval: timedelta) -> list[datetime]:
    opens: list[datetime] = []
    current = start
    while current < end:
        opens.append(current)
        current += interval
    return opens


def _iter_dates(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _stop_exit(side: str, bar: Bar, stop: float) -> tuple[float, str] | None:
    if side == "long":
        if bar.open <= stop:
            return bar.open, "protective_stop_gap"
        if bar.low <= stop:
            return stop, "protective_stop"
        return None
    if bar.open >= stop:
        return bar.open, "protective_stop_gap"
    if bar.high >= stop:
        return stop, "protective_stop"
    return None


def _summaries(trades: list[Trade]) -> dict[str, Any]:
    ordered = sorted(trades, key=lambda trade: trade.entry_ts)
    overall = summarize_pnls([trade.gross_R for trade in ordered], initial_capital=0.0)
    by_side: dict[str, Any] = {}
    for side in ("long", "short"):
        rows = [trade for trade in ordered if trade.side == side]
        by_side[side] = summarize_pnls([trade.gross_R for trade in rows], initial_capital=0.0)

    month_groups: dict[str, list[Trade]] = defaultdict(list)
    for trade in ordered:
        month_groups[trade.session_date[:7]].append(trade)
    by_month: dict[str, Any] = {}
    positive_months = 0
    for month in sorted(month_groups):
        metrics = summarize_pnls([trade.gross_R for trade in month_groups[month]], initial_capital=0.0)
        by_month[month] = metrics
        if float(metrics["net_profit"]) > 0:
            positive_months += 1

    regime_groups: dict[str, list[Trade]] = defaultdict(list)
    for trade in ordered:
        regime_groups[trade.regime or "unlabeled"].append(trade)
    by_regime = {
        regime: summarize_pnls([trade.gross_R for trade in rows], initial_capital=0.0)
        for regime, rows in sorted(regime_groups.items())
    }
    return {
        "overall": overall,
        "by_side": by_side,
        "by_month": by_month,
        "eligible_month_count": len(by_month),
        "positive_month_count": positive_months,
        "by_regime": by_regime,
    }


def _acceptance(summary: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]:
    criteria = strategy["acceptance_criteria_for_signal_research"]
    overall = summary["overall"]
    by_side = summary["by_side"]
    pf = overall.get("profit_factor")
    checks = {
        "minimum_total_trades": int(overall["trades"]) >= int(criteria["minimum_total_trades"]),
        "minimum_long_trades": int(by_side["long"]["trades"]) >= int(criteria["minimum_long_trades"]),
        "minimum_short_trades": int(by_side["short"]["trades"]) >= int(criteria["minimum_short_trades"]),
        "gross_expectancy_R_positive": overall.get("expectancy") is not None
        and float(overall["expectancy"]) > float(criteria["gross_expectancy_R_must_be_greater_than"]),
        "gross_profit_factor_above_one": pf is not None and float(pf) > float(criteria["gross_profit_factor_must_be_greater_than"]),
        "minimum_positive_months": int(summary["positive_month_count"])
        >= int(criteria["minimum_positive_months_out_of_eligible_months"]),
    }
    return {
        "checks": checks,
        "passed": all(checks.values()),
        "failure_action": criteria["failure_action"],
        "optimization_permitted_after_failure": False,
    }


def _regime_map(csv_path: str | Path, repo_root: Path) -> dict[str, str]:
    result = run_named_session_tpo_regime_robustness(csv_path, repo_root=repo_root)
    assignments = result["regime_robustness"]["date_assignments"]
    return {str(item["current_paired_date"]): str(item["regime"]) for item in assignments}


def run_strategy_signal_backtest(
    csv_path: str | Path,
    *,
    strategy_spec_path: str | Path = "quant/candidates/XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.strategy.yaml",
    evaluation_spec_path: str | Path = "quant/candidates/XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.evaluation.yaml",
    repo_root: str | Path = ".",
    include_regime_reporting: bool = True,
) -> dict[str, Any]:
    root = Path(repo_root)
    strategy_path = Path(strategy_spec_path)
    if not strategy_path.is_absolute():
        strategy_path = root / strategy_path
    evaluation_path = Path(evaluation_spec_path)
    if not evaluation_path.is_absolute():
        evaluation_path = root / evaluation_path

    strategy_validation = validate_strategy_spec(strategy_path, root)
    if strategy_validation.errors:
        raise ValueError("invalid strategy specification: " + "; ".join(strategy_validation.errors))
    evaluation_validation = validate_signal_evaluation_file(evaluation_path, root)
    if evaluation_validation.errors:
        raise ValueError("invalid signal evaluation specification: " + "; ".join(evaluation_validation.errors))

    strategy = _load_yaml(strategy_path)
    evaluation = _load_yaml(evaluation_path)
    cutoff = datetime.fromisoformat(str(strategy["data"]["cutoff_utc"]).replace("Z", "+00:00")).astimezone(UTC)
    policy_path = root / str(strategy["session_context"]["policy_path"])
    policy = NamedSessionPolicy.from_yaml(policy_path)
    bars, csv_meta = _load_closed_bars(csv_path, cutoff, strategy["data"]["timeframe"])
    if not bars:
        raise ValueError("no closed bars at cutoff")
    by_ts = {bar.ts: bar for bar in bars}
    interval = timedelta(minutes=5)

    ny_def = policy.definitions["new_york"]
    ny_zone = ZoneInfo(ny_def.timezone_name)
    local_first = bars[0].ts.astimezone(ny_zone).date() - timedelta(days=1)
    local_last = cutoff.astimezone(ny_zone).date() + timedelta(days=1)

    regime_by_date: dict[str, str] = {}
    if include_regime_reporting:
        regime_by_date = _regime_map(csv_path, root)

    trades: list[Trade] = []
    skipped: dict[str, int] = defaultdict(int)
    evaluated_sessions = 0
    candidate_sessions = 0

    for local_date in _iter_dates(local_first, local_last):
        if local_date.weekday() not in ny_def.weekdays:
            continue
        ny_start, ny_end = policy.bounds_utc("new_york", local_date)
        if ny_end <= bars[0].ts or ny_start > cutoff:
            continue
        candidate_sessions += 1
        if ny_end > cutoff:
            skipped["coverage_edge_or_session_not_closed"] += 1
            continue

        ny_opens = _expected_opens(ny_start, ny_end, interval)
        if len(ny_opens) != int(evaluation["data"]["expected_new_york_m5_bars"]):
            skipped["unexpected_session_bar_count"] += 1
            continue
        if any(ts not in by_ts for ts in ny_opens):
            skipped["incomplete_new_york_session"] += 1
            continue

        ref_minutes = int(strategy["baseline_parameters"]["pre_ny_reference_minutes"])
        ref_start = ny_start - timedelta(minutes=ref_minutes)
        ref_opens = _expected_opens(ref_start, ny_start, interval)
        if len(ref_opens) != int(strategy["reference_range"]["expected_m5_bars"]):
            skipped["unexpected_reference_bar_count"] += 1
            continue
        if any(ts not in by_ts for ts in ref_opens):
            skipped["incomplete_reference_range"] += 1
            continue
        if any(not policy.contains("london", ts) for ts in ref_opens):
            skipped["reference_not_fully_london"] += 1
            continue

        reference = [by_ts[ts] for ts in ref_opens]
        ref_high = max(bar.high for bar in reference)
        ref_low = min(bar.low for bar in reference)
        if ref_high <= ref_low:
            skipped["non_positive_reference_range"] += 1
            continue
        evaluated_sessions += 1

        trigger_end = ny_start + timedelta(minutes=int(strategy["baseline_parameters"]["trigger_window_minutes"]))
        trigger_opens = [ts for ts in ny_opens if ts < trigger_end]
        trigger: tuple[str, Bar] | None = None
        for ts in trigger_opens:
            bar = by_ts[ts]
            if bar.close > ref_high:
                trigger = ("long", bar)
                break
            if bar.close < ref_low:
                trigger = ("short", bar)
                break
        if trigger is None:
            skipped["no_trigger"] += 1
            continue

        side, trigger_bar = trigger
        entry_ts = trigger_bar.ts + interval
        if entry_ts not in by_ts or not (ny_start <= entry_ts < ny_end):
            skipped["next_bar_fill_unavailable"] += 1
            continue
        entry_bar = by_ts[entry_ts]
        entry = entry_bar.open
        stop = ref_low if side == "long" else ref_high
        risk = entry - stop if side == "long" else stop - entry
        if risk <= 0:
            skipped["non_positive_initial_risk"] += 1
            continue

        exit_price: float | None = None
        exit_ts: datetime | None = None
        exit_reason: str | None = None
        for ts in ny_opens:
            if ts < entry_ts:
                continue
            bar = by_ts[ts]
            stop_result = _stop_exit(side, bar, stop)
            if stop_result is not None:
                exit_price, exit_reason = stop_result
                exit_ts = ts if exit_reason == "protective_stop_gap" else ts + interval
                break
        if exit_price is None:
            final_bar = by_ts[ny_opens[-1]]
            exit_price = final_bar.close
            exit_ts = ny_end
            exit_reason = "session_time_exit"

        gross_R = (exit_price - entry) / risk if side == "long" else (entry - exit_price) / risk
        trades.append(
            Trade(
                session_date=local_date.isoformat(),
                side=side,
                trigger_close_ts=trigger_bar.ts + interval,
                entry_ts=entry_ts,
                entry_price=entry,
                stop_price=stop,
                exit_ts=exit_ts,
                exit_price=exit_price,
                exit_reason=exit_reason,
                initial_risk=risk,
                gross_R=gross_R,
                reference_high=ref_high,
                reference_low=ref_low,
                regime=regime_by_date.get(local_date.isoformat()),
            )
        )

    trades.sort(key=lambda trade: trade.entry_ts)
    summary = _summaries(trades)
    acceptance = _acceptance(summary, strategy)
    return {
        "backtest_class": "gross_signal_research_v1",
        "strategy_spec_id": strategy["spec_id"],
        "evaluation_id": evaluation["evaluation_id"],
        "dataset_id": strategy["data"]["dataset_id"],
        "input_csv": str(Path(csv_path)),
        "input_csv_meta": csv_meta,
        "cutoff_utc": cutoff.isoformat(),
        "session_policy_id": policy.policy_id,
        "candidate_sessions": candidate_sessions,
        "evaluated_sessions": evaluated_sessions,
        "trade_count": len(trades),
        "skipped_session_or_signal_counts": dict(sorted(skipped.items())),
        "trade_ledger": [trade.as_dict() for trade in trades],
        "metrics": summary,
        "acceptance": acceptance,
        "interpretation_boundaries": {
            "gross_zero_cost_only": True,
            "net_profitability_not_tested": True,
            "regime_reporting_only": True,
            "strategy_not_promoted_to_live": True,
            "failure_must_not_trigger_parameter_tuning": True,
        },
    }
