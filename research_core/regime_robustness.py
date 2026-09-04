from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any
import math

import yaml

from .regime_robustness_validation import validate_regime_robustness_spec
from .tpo_study import run_named_session_tpo_study


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _quantile_linear(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("quantile requires at least one value")
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _summarize(values: list[float]) -> dict[str, float | int]:
    if not values:
        raise ValueError("summary requires at least one value")
    values_f = [float(value) for value in values]
    return {
        "n": len(values_f),
        "min": min(values_f),
        "q25": _quantile_linear(values_f, 0.25),
        "median": _quantile_linear(values_f, 0.50),
        "q75": _quantile_linear(values_f, 0.75),
        "max": max(values_f),
        "mean": sum(values_f) / len(values_f),
    }


def _date_from_instance_id(instance_id: str) -> str:
    try:
        date_part = instance_id.rsplit(":", 1)[1]
    except IndexError as exc:
        raise ValueError(f"invalid session_instance_id: {instance_id!r}") from exc
    if len(date_part) != 10 or date_part[4] != "-" or date_part[7] != "-":
        raise ValueError(f"session_instance_id does not end in YYYY-MM-DD: {instance_id!r}")
    return date_part


def _direction(left: float, right: float, left_session: str, right_session: str) -> str:
    if math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12):
        return "tie"
    if left > right:
        return f"{left_session}_gt_{right_session}"
    return f"{right_session}_gt_{left_session}"


def _lagged_percentile(values: list[float], target: float) -> Fraction:
    if not values:
        raise ValueError("rank window cannot be empty")
    less = sum(1 for value in values if value < target)
    equal = sum(1 for value in values if math.isclose(value, target, rel_tol=1e-12, abs_tol=1e-12))
    return Fraction(2 * less + equal, 2 * len(values))


def _label_from_percentile(percentile: Fraction) -> str:
    if percentile < Fraction(1, 3):
        return "low"
    if percentile < Fraction(2, 3):
        return "normal"
    return "high"


def assign_lagged_range_regimes(
    feature_rows: dict[str, list[dict[str, Any]]],
    spec: dict[str, Any],
) -> dict[str, Any]:
    regime = spec["regime_robustness"]
    pair = list(spec["comparison_policy"]["primary_pair"])
    if len(pair) != 2:
        raise ValueError("regime robustness requires exactly two primary sessions")
    left, right = pair
    lookback = int(regime["lookback_paired_dates"])
    minimum_pair_n = int(regime["minimum_pair_n_per_regime"])
    features = list(spec["features"])
    directional_features = list(regime["directional_features"])
    labels = list(regime["labels"])

    rows_by_date: dict[str, dict[str, dict[str, Any]]] = {}
    for session_id in pair:
        session_map: dict[str, dict[str, Any]] = {}
        for row in feature_rows.get(session_id, []):
            date_key = _date_from_instance_id(str(row["session_instance_id"]))
            if date_key in session_map:
                raise ValueError(f"duplicate paired session date for {session_id}: {date_key}")
            session_map[date_key] = row
        rows_by_date[session_id] = session_map

    paired_dates = sorted(set(rows_by_date[left]) & set(rows_by_date[right]))
    composite_by_date = {
        date_key: (
            float(rows_by_date[left][date_key]["range_ticks"])
            + float(rows_by_date[right][date_key]["range_ticks"])
        )
        / 2.0
        for date_key in paired_dates
    }

    regime_rows: dict[str, dict[str, list[dict[str, Any]]]] = {
        label: {left: [], right: []} for label in labels
    }
    assignments: list[dict[str, Any]] = []

    for index in range(lookback, len(paired_dates)):
        current_date = paired_dates[index]
        prior_dates = paired_dates[index - lookback:index]
        target_date = prior_dates[-1]
        window_values = [composite_by_date[date_key] for date_key in prior_dates]
        target_value = composite_by_date[target_date]
        percentile = _lagged_percentile(window_values, target_value)
        label = _label_from_percentile(percentile)
        if label not in regime_rows:
            raise ValueError(f"computed unknown regime label: {label}")

        regime_rows[label][left].append(rows_by_date[left][current_date])
        regime_rows[label][right].append(rows_by_date[right][current_date])
        assignments.append(
            {
                "current_paired_date": current_date,
                "lagged_target_date": target_date,
                "lookback_paired_dates": lookback,
                "lagged_target_composite_range_ticks": target_value,
                "midrank_percentile": float(percentile),
                "regime": label,
            }
        )

    buckets: dict[str, Any] = {}
    eligible_labels: list[str] = []
    for label in labels:
        session_rows = regime_rows[label]
        counts = {session_id: len(session_rows[session_id]) for session_id in pair}
        eligible = all(counts[session_id] >= minimum_pair_n for session_id in pair)
        if eligible:
            eligible_labels.append(label)

        summaries: dict[str, Any] = {}
        for session_id in pair:
            rows = session_rows[session_id]
            session_features: dict[str, Any] = {}
            for feature in features:
                values = [float(row[feature]) for row in rows]
                session_features[feature] = _summarize(values) if values else None
            summaries[session_id] = {"n": len(rows), "features": session_features}

        comparisons: dict[str, Any] = {}
        for feature in features:
            left_summary = summaries[left]["features"][feature]
            right_summary = summaries[right]["features"][feature]
            if left_summary is None or right_summary is None:
                continue
            left_median = float(left_summary["median"])
            right_median = float(right_summary["median"])
            comparisons[feature] = {
                "left_session": left,
                "right_session": right,
                "median_difference_left_minus_right": left_median - right_median,
                "median_ratio_left_over_right": left_median / right_median if right_median != 0 else None,
                "direction": _direction(left_median, right_median, left, right),
            }

        buckets[label] = {
            "eligible": eligible,
            "minimum_pair_n": minimum_pair_n,
            "counts": counts,
            "session_summaries": summaries,
            "comparison": comparisons,
        }

    reference = spec["follow_up_design"]["base_observed_direction_reference"]
    persistence: dict[str, Any] = {}
    for feature in directional_features:
        expected = str(reference[feature])
        matches = 0
        observed = 0
        for label in eligible_labels:
            comparison_record = buckets[label]["comparison"].get(feature)
            if not isinstance(comparison_record, dict):
                continue
            observed += 1
            if comparison_record.get("direction") == expected:
                matches += 1
        persistence[feature] = {
            "base_direction": expected,
            "eligible_regime_count": observed,
            "matching_direction_regime_count": matches,
            "matching_direction_fraction": matches / observed if observed else None,
        }

    return {
        "regime_id": regime["regime_id"],
        "regime_class": regime["regime_class"],
        "canonical_market_regime_claim": False,
        "pairing_key": regime["pairing_key"],
        "paired_date_count": len(paired_dates),
        "warmup_excluded_paired_dates": min(lookback, len(paired_dates)),
        "labeled_paired_date_count": len(assignments),
        "lookback_paired_dates": lookback,
        "percentile_method": regime["percentile_method"],
        "thresholds": dict(regime["thresholds"]),
        "minimum_pair_n_per_regime": minimum_pair_n,
        "eligible_regime_count": len(eligible_labels),
        "eligible_regimes": eligible_labels,
        "regime_buckets": buckets,
        "directional_persistence": persistence,
        "date_assignments": assignments,
        "statistical_significance_test": "none",
    }


def run_named_session_tpo_regime_robustness(
    csv_path: str | Path,
    *,
    spec_path: str | Path = "quant/studies/XAUUSD_NAMED_SESSION_TPO_REGIME_ROBUSTNESS_V1.yaml",
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    root = Path(repo_root)
    spec_file = Path(spec_path)
    if not spec_file.is_absolute():
        spec_file = root / spec_file

    validation = validate_regime_robustness_spec(spec_file, root)
    if validation.errors:
        raise ValueError("invalid regime robustness specification: " + "; ".join(validation.errors))
    spec = _load_yaml(spec_file)

    base = run_named_session_tpo_study(
        csv_path,
        spec_path=spec_file,
        repo_root=root,
        include_rows=True,
    )
    feature_rows = base.pop("feature_rows")
    regime_result = assign_lagged_range_regimes(feature_rows, spec)

    follow = spec["follow_up_design"]
    return {
        "study_id": spec["study_id"],
        "spec_status": spec["status"],
        "study_type": spec["study_type"],
        "declared_follow_up": True,
        "base_study_id": follow["base_study_id"],
        "base_result_path": follow["base_result_path"],
        "dataset_id": spec["data"]["dataset_id"],
        "input_csv": str(Path(csv_path)),
        "timeframe": spec["data"]["timeframe"],
        "cutoff_utc": spec["data"]["cutoff_utc"],
        "session_policy_id": spec["session_context"]["policy_id"],
        "selection_policy": dict(spec["session_context"]["selection"]),
        "operational_rule_id": spec["operational_input"]["rule_id"],
        "price_increment": str(spec["operational_input"]["price_increment"]),
        "aggregate_reference": base,
        "regime_robustness": regime_result,
        "interpretation_boundaries": {
            **dict(spec["interpretation_boundaries"]),
            "statistical_significance_not_tested": True,
            "regime_definition_is_project_defined": True,
            "regime_conditioning_is_causal_lagged_only": True,
        },
    }
