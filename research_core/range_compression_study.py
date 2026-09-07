from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
import json
import math
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

import yaml

from .data_validation import TIMEFRAME_SECONDS
from .range_compression_study_validation import validate_range_compression_study_spec
from .session_policy import NamedSessionPolicy
from .strategy_signal_backtest import _load_closed_bars


UTC = timezone.utc
LOOKBACK_ELIGIBLE_REFERENCE_WIDTHS = 20
COMPRESSION_BUCKETS = ("compressed", "normal", "expanded")
REPORT_SIDES = ("long", "short")
STOP_EXIT_REASONS = {"protective_stop", "protective_stop_gap"}


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


def _repo_path(root: Path, value: Any) -> Path:
    path = Path(str(value).replace("\\", "/"))
    return path if path.is_absolute() else root / path


def _aware_datetime(value: Any) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"expected timezone-aware ISO-8601 timestamp, got {value!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"expected timezone-aware ISO-8601 timestamp, got {value!r}")
    return parsed.astimezone(UTC)


def _iter_dates(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _expected_opens(start: datetime, end: datetime, interval: timedelta) -> list[datetime]:
    result: list[datetime] = []
    current = start
    while current < end:
        result.append(current)
        current += interval
    return result


def _is_close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12)


def midrank_percentile(current_reference_width: float, prior_reference_widths: Iterable[float]) -> float:
    """Rank the current width against a non-empty prior-only window using midranks."""
    current = float(current_reference_width)
    if not math.isfinite(current):
        raise ValueError("current reference width must be finite")
    prior = [float(value) for value in prior_reference_widths]
    if not prior:
        raise ValueError("midrank percentile requires at least one prior reference width")
    if any(not math.isfinite(value) for value in prior):
        raise ValueError("prior reference widths must be finite")

    less = 0
    equal = 0
    for value in prior:
        if _is_close(value, current):
            equal += 1
        elif value < current:
            less += 1
    return float(Fraction(2 * less + equal, 2 * len(prior)))


def compression_bucket(percentile: float) -> str:
    """Apply the frozen thirds without tuning or data-dependent thresholding."""
    value = float(percentile)
    if not math.isfinite(value) or value < 0.0 or value > 1.0:
        raise ValueError("percentile must be finite and within [0, 1]")
    if value < 1.0 / 3.0:
        return "compressed"
    if value < 2.0 / 3.0:
        return "normal"
    return "expanded"


def annotate_reference_width_history(
    reference_rows: Iterable[Mapping[str, Any]],
    *,
    lookback: int = LOOKBACK_ELIGIBLE_REFERENCE_WIDTHS,
) -> list[dict[str, Any]]:
    """Add causal trailing-only width features to every eligible reference-range date.

    A current row may be the rank target, but its width is intentionally absent from both the
    trailing median and the comparator window. Calendar gaps do not matter: history advances only
    across eligible reference-width observations.
    """
    if lookback != LOOKBACK_ELIGIBLE_REFERENCE_WIDTHS:
        raise ValueError("lookback is frozen at 20 eligible reference widths")

    copied_rows = [dict(row) for row in reference_rows]
    dates = [str(row.get("session_date", "")) for row in copied_rows]
    if any(not value for value in dates):
        raise ValueError("every reference-width row requires session_date")
    if dates != sorted(dates) or len(set(dates)) != len(dates):
        raise ValueError("eligible reference-width rows must have unique, ascending session_date values")

    widths: list[float] = []
    for row in copied_rows:
        if "reference_high" not in row or "reference_low" not in row:
            raise ValueError("every reference-width row requires reference_high and reference_low")
        reference_high = float(row["reference_high"])
        reference_low = float(row["reference_low"])
        declared_width = float(row.get("current_reference_width"))
        computed_width = reference_high - reference_low
        if not _is_close(declared_width, computed_width):
            raise ValueError("current_reference_width must equal reference_high - reference_low")
        width = computed_width
        if not math.isfinite(width) or width <= 0.0:
            raise ValueError("eligible reference widths must be finite and positive")
        widths.append(width)

    result: list[dict[str, Any]] = []
    for index, row in enumerate(copied_rows):
        current_width = widths[index]
        enriched = {
            **row,
            "eligible_reference_width_index": index,
            "current_reference_width": current_width,
            "lagged_20_reference_width_median": None,
            "relative_range_ratio": None,
            "reference_width_midrank_percentile": None,
            "compression_bucket": None,
            "causal_feature_status": "unassigned_warmup_insufficient_prior_eligible_widths",
        }
        if index >= lookback:
            prior_widths = widths[index - lookback:index]
            baseline = float(median(prior_widths))
            if baseline <= 0.0:
                raise ValueError("lagged reference-width median must be positive")
            percentile = midrank_percentile(current_width, prior_widths)
            enriched.update(
                {
                    "lagged_20_reference_width_median": baseline,
                    "relative_range_ratio": current_width / baseline,
                    "reference_width_midrank_percentile": percentile,
                    "compression_bucket": compression_bucket(percentile),
                    "causal_feature_status": "assigned_causal_prior_only",
                }
            )
        result.append(enriched)
    return result


def breakout_penetration(trade: Mapping[str, Any]) -> float:
    side = str(trade.get("side", "")).lower()
    entry = float(trade["entry_price"])
    reference_high = float(trade["reference_high"])
    reference_low = float(trade["reference_low"])
    if side == "long":
        return entry - reference_high
    if side == "short":
        return reference_low - entry
    raise ValueError(f"unsupported trade side: {trade.get('side')!r}")


def _reporting_regime(value: Any) -> str:
    text = str(value or "").strip()
    return text if text else "unlabeled"


def annotate_trade_ledger(
    trade_ledger: Iterable[Mapping[str, Any]],
    reference_width_history: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Decorate every source trade; warmup trades remain in the output and are never filtered."""
    history_by_date = {
        str(row["session_date"]): dict(row)
        for row in reference_width_history
    }
    if not history_by_date:
        raise ValueError("reference-width history cannot be empty")

    result: list[dict[str, Any]] = []
    seen_dates: set[str] = set()
    for index, raw_trade in enumerate(trade_ledger):
        trade = dict(raw_trade)
        session_date = str(trade.get("session_date", ""))
        if not session_date:
            raise ValueError(f"trade_ledger[{index}] is missing session_date")
        if session_date in seen_dates:
            raise ValueError("source trade ledger has duplicate session_date values")
        seen_dates.add(session_date)
        reference = history_by_date.get(session_date)
        if reference is None:
            raise ValueError(f"source trade {session_date} lacks a reconstructed eligible reference width")

        source_high = float(trade["reference_high"])
        source_low = float(trade["reference_low"])
        if not _is_close(source_high, float(reference["reference_high"])) or not _is_close(
            source_low, float(reference["reference_low"])
        ):
            raise ValueError(f"source trade {session_date} reference range disagrees with reconstructed frozen range")

        width = float(reference["current_reference_width"])
        penetration = breakout_penetration(trade)
        result.append(
            {
                **trade,
                "source_trade_ledger_index": index,
                "regime_reporting_label": _reporting_regime(trade.get("regime")),
                "current_reference_width": width,
                "lagged_20_reference_width_median": reference["lagged_20_reference_width_median"],
                "relative_range_ratio": reference["relative_range_ratio"],
                "reference_width_midrank_percentile": reference["reference_width_midrank_percentile"],
                "compression_bucket": reference["compression_bucket"],
                "causal_feature_status": reference["causal_feature_status"],
                "breakout_penetration": penetration,
                "penetration_ratio": penetration / width,
            }
        )
    return result


def summarize_descriptive_cell(trades: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize a descriptive cell with no inferential or profitability interpretation."""
    rows = list(trades)
    values = [float(row["gross_R"]) for row in rows]
    count = len(values)
    if count == 0:
        return {
            "trades": 0,
            "net_R": 0.0,
            "expectancy_R": None,
            "profit_factor": None,
            "win_rate": None,
            "stop_rate": None,
            "average_R": None,
            "median_R": None,
            "cell_status": "underpowered_descriptive_only",
        }

    gross_profit = sum(value for value in values if value > 0.0)
    gross_loss = -sum(value for value in values if value < 0.0)
    net_r = sum(values)
    wins = sum(value > 0.0 for value in values)
    stops = sum(str(row.get("exit_reason", "")) in STOP_EXIT_REASONS for row in rows)
    return {
        "trades": count,
        "net_R": net_r,
        "expectancy_R": net_r / count,
        "profit_factor": (gross_profit / gross_loss) if gross_loss > 0.0 else None,
        "win_rate": wins / count,
        "stop_rate": stops / count,
        "average_R": net_r / count,
        "median_R": float(median(values)),
        "cell_status": "underpowered_descriptive_only" if count < 10 else "descriptive_only",
    }


def build_descriptive_breakdowns(annotated_trades: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Produce all frozen breakdowns; only unassignable warmup rows lack a bucket cell."""
    rows = [dict(row) for row in annotated_trades]
    assigned = [row for row in rows if row.get("compression_bucket") in COMPRESSION_BUCKETS]

    by_side = {
        side: summarize_descriptive_cell(row for row in rows if str(row.get("side")).lower() == side)
        for side in REPORT_SIDES
    }
    by_bucket = {
        bucket: summarize_descriptive_cell(row for row in assigned if row.get("compression_bucket") == bucket)
        for bucket in COMPRESSION_BUCKETS
    }
    by_side_x_bucket = {
        side: {
            bucket: summarize_descriptive_cell(
                row
                for row in assigned
                if str(row.get("side")).lower() == side and row.get("compression_bucket") == bucket
            )
            for bucket in COMPRESSION_BUCKETS
        }
        for side in REPORT_SIDES
    }
    regimes = sorted({_reporting_regime(row.get("regime")) for row in rows})
    by_regime_x_side_x_bucket = {
        regime: {
            side: {
                bucket: summarize_descriptive_cell(
                    row
                    for row in assigned
                    if _reporting_regime(row.get("regime")) == regime
                    and str(row.get("side")).lower() == side
                    and row.get("compression_bucket") == bucket
                )
                for bucket in COMPRESSION_BUCKETS
            }
            for side in REPORT_SIDES
        }
        for regime in regimes
    }
    return {
        "overall": summarize_descriptive_cell(rows),
        "by_side": by_side,
        "by_compression_bucket": by_bucket,
        "side_x_compression_bucket": by_side_x_bucket,
        "regime_x_side_x_compression_bucket": by_regime_x_side_x_bucket,
    }


def _reconstruct_eligible_reference_widths(
    spec: Mapping[str, Any],
    strategy: Mapping[str, Any],
    evaluation: Mapping[str, Any],
    source_backtest: Mapping[str, Any],
    root: Path,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    data = spec["data"]
    source_path = _repo_path(root, data["m5_bars_path"])
    cutoff = _aware_datetime(data["cutoff_utc"])
    timeframe = str(data["timeframe"])
    bars, _ = _load_closed_bars(source_path, cutoff, timeframe)
    if not bars:
        raise ValueError("bound M5 source has no closed bars at the frozen cutoff")
    interval = timedelta(seconds=TIMEFRAME_SECONDS[timeframe.upper()])
    by_timestamp = {bar.ts: bar for bar in bars}

    policy_path = _repo_path(root, strategy["session_context"]["policy_path"])
    policy = NamedSessionPolicy.from_yaml(policy_path)
    ny_definition = policy.definitions["new_york"]
    ny_zone = ZoneInfo(ny_definition.timezone_name)
    local_first = bars[0].ts.astimezone(ny_zone).date() - timedelta(days=1)
    local_last = cutoff.astimezone(ny_zone).date() + timedelta(days=1)

    expected_ny_bars = int(evaluation["data"]["expected_new_york_m5_bars"])
    expected_reference_bars = int(strategy["reference_range"]["expected_m5_bars"])
    reference_minutes = int(strategy["baseline_parameters"]["pre_ny_reference_minutes"])
    skipped: dict[str, int] = defaultdict(int)
    candidate_sessions = 0
    reference_rows: list[dict[str, Any]] = []

    for local_date in _iter_dates(local_first, local_last):
        if local_date.weekday() not in ny_definition.weekdays:
            continue
        ny_start, ny_end = policy.bounds_utc("new_york", local_date)
        if ny_end <= bars[0].ts or ny_start > cutoff:
            continue
        candidate_sessions += 1
        if ny_end > cutoff:
            skipped["coverage_edge_or_session_not_closed"] += 1
            continue

        ny_opens = _expected_opens(ny_start, ny_end, interval)
        if len(ny_opens) != expected_ny_bars:
            skipped["unexpected_session_bar_count"] += 1
            continue
        if any(timestamp not in by_timestamp for timestamp in ny_opens):
            skipped["incomplete_new_york_session"] += 1
            continue

        reference_start = ny_start - timedelta(minutes=reference_minutes)
        reference_opens = _expected_opens(reference_start, ny_start, interval)
        if len(reference_opens) != expected_reference_bars:
            skipped["unexpected_reference_bar_count"] += 1
            continue
        if any(timestamp not in by_timestamp for timestamp in reference_opens):
            skipped["incomplete_reference_range"] += 1
            continue
        if any(not policy.contains("london", timestamp) for timestamp in reference_opens):
            skipped["reference_not_fully_london"] += 1
            continue

        reference_bars = [by_timestamp[timestamp] for timestamp in reference_opens]
        reference_high = max(bar.high for bar in reference_bars)
        reference_low = min(bar.low for bar in reference_bars)
        current_width = reference_high - reference_low
        if current_width <= 0.0:
            skipped["non_positive_reference_range"] += 1
            continue
        reference_rows.append(
            {
                "session_date": local_date.isoformat(),
                "reference_high": reference_high,
                "reference_low": reference_low,
                "current_reference_width": current_width,
            }
        )

    expected_evaluated = int(source_backtest["evaluated_sessions"])
    if len(reference_rows) != expected_evaluated:
        raise ValueError(
            "reconstructed eligible reference-width count does not match bound source backtest "
            f"evaluated_sessions ({len(reference_rows)} != {expected_evaluated})"
        )
    return reference_rows, {
        "candidate_sessions": candidate_sessions,
        "eligible_reference_width_count": len(reference_rows),
        "skipped_session_counts": dict(sorted(skipped.items())),
    }


def run_range_compression_study(
    *,
    spec_path: str | Path = "quant/studies/XAUUSD_NY_PREOPEN_RANGE_COMPRESSION_EXPLORATORY_V1.yaml",
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    """Run the frozen post-hoc diagnostic without changing or filtering the bound source trades."""
    root = Path(repo_root)
    spec_file = _repo_path(root, spec_path)
    validation = validate_range_compression_study_spec(spec_file, root)
    if validation.errors:
        raise ValueError("invalid range-compression study specification: " + "; ".join(validation.errors))
    spec = _load_yaml(spec_file)
    binding = spec["source_binding"]

    source_backtest = _load_json(_repo_path(root, binding["source_backtest_path"]))
    strategy = _load_yaml(_repo_path(root, binding["strategy_spec_path"]))
    evaluation = _load_yaml(_repo_path(root, binding["evaluation_spec_path"]))
    raw_reference_history, reconstruction = _reconstruct_eligible_reference_widths(
        spec,
        strategy,
        evaluation,
        source_backtest,
        root,
    )
    reference_history = annotate_reference_width_history(raw_reference_history)
    annotated_trades = annotate_trade_ledger(source_backtest["trade_ledger"], reference_history)
    if len(annotated_trades) != len(source_backtest["trade_ledger"]):
        raise ValueError("all source trades must be retained in the annotated trade ledger")

    breakdowns = build_descriptive_breakdowns(annotated_trades)
    assigned = [row for row in annotated_trades if row.get("compression_bucket") in COMPRESSION_BUCKETS]
    warmup = [row for row in annotated_trades if row.get("compression_bucket") is None]
    return {
        "study_id": spec["study_id"],
        "study_name": spec["study_name"],
        "study_class": spec["study_class"],
        "status": spec["status"],
        "source_binding": {
            "source_repository_baseline_commit": spec["source_repository_baseline_commit"],
            "source_backtest_sha256": spec["source_backtest_sha256"],
            "source_backtest_path": binding["source_backtest_path"],
            "strategy_spec_id": binding["strategy_spec_id"],
            "strategy_spec_sha256": binding["strategy_spec_sha256"],
            "dataset_id": spec["data"]["dataset_id"],
            "dataset_manifest": spec["data"]["dataset_manifest"],
            "m5_bars_path": spec["data"]["m5_bars_path"],
            "m5_bars_sha256": spec["data"]["m5_bars_sha256"],
        },
        "causal_feature_definition": {
            "lookback_eligible_reference_widths": LOOKBACK_ELIGIBLE_REFERENCE_WIDTHS,
            "lagged_baseline": "median of immediately preceding 20 eligible reference widths",
            "current_date_in_lagged_baseline": False,
            "rank": "current reference width against prior 20 eligible widths only using midrank percentile",
            "buckets": list(COMPRESSION_BUCKETS),
        },
        "reference_width_reconstruction": reconstruction,
        "reference_width_history": reference_history,
        "assignment_coverage": {
            "source_trade_count": len(source_backtest["trade_ledger"]),
            "reported_trade_count": len(annotated_trades),
            "compression_assigned_trade_count": len(assigned),
            "unassigned_warmup_trade_count": len(warmup),
            "unassigned_warmup_session_dates": [row["session_date"] for row in warmup],
            "unassigned_warmup_descriptive_cell": summarize_descriptive_cell(warmup),
            "trade_filtering_applied": False,
        },
        "breakdowns": breakdowns,
        "annotated_trade_ledger": annotated_trades,
        "interpretation_boundaries": dict(spec["interpretation_boundaries"]),
        "reporting_note": (
            "All bound source trades are retained. Bucket-specific cells exclude only causal warmup rows "
            "whose frozen 20-prior-width feature is undefined; their descriptive reconciliation cell is "
            "reported separately, not used as a trade filter."
        ),
    }
