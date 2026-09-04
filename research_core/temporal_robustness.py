from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any
import math

import yaml

from .study_result_validation import validate_study_result
from .study_spec_validation import validate_study_spec
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


def _month_from_instance_id(instance_id: str) -> str:
    try:
        date_part = instance_id.rsplit(":", 1)[1]
    except IndexError as exc:
        raise ValueError(f"invalid session_instance_id: {instance_id!r}") from exc
    if len(date_part) < 7 or date_part[4] != "-":
        raise ValueError(f"session_instance_id does not end in YYYY-MM-DD: {instance_id!r}")
    return date_part[:7]


def _direction(left: float, right: float, left_session: str, right_session: str) -> str:
    if math.isclose(left, right, rel_tol=1e-12, abs_tol=1e-12):
        return "tie"
    if left > right:
        return f"{left_session}_gt_{right_session}"
    return f"{right_session}_gt_{left_session}"


def summarize_temporal_feature_rows(
    feature_rows: dict[str, list[dict[str, Any]]],
    spec: dict[str, Any],
) -> dict[str, Any]:
    temporal = spec["temporal_robustness"]
    comparison = spec["comparison_policy"]
    pair = list(comparison["primary_pair"])
    if len(pair) != 2:
        raise ValueError("temporal robustness requires exactly two primary sessions")
    left, right = pair
    features = list(spec["features"])
    directional_features = list(temporal["directional_features"])
    minimum_pair_n = int(temporal["minimum_pair_n_per_bucket"])

    by_month: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for session_id, rows in feature_rows.items():
        for row in rows:
            month = _month_from_instance_id(str(row["session_instance_id"]))
            by_month[month][session_id].append(row)

    month_buckets: dict[str, Any] = {}
    eligible_months: list[str] = []
    for month in sorted(by_month):
        month_sessions = by_month[month]
        counts = {session: len(month_sessions.get(session, [])) for session in pair}
        eligible = all(counts[session] >= minimum_pair_n for session in pair)
        if eligible:
            eligible_months.append(month)

        summaries: dict[str, Any] = {}
        for session in pair:
            rows = month_sessions.get(session, [])
            session_features: dict[str, Any] = {}
            for feature in features:
                values = [float(row[feature]) for row in rows]
                session_features[feature] = _summarize(values) if values else None
            summaries[session] = {"n": len(rows), "features": session_features}

        feature_comparisons: dict[str, Any] = {}
        for feature in features:
            left_summary = summaries[left]["features"][feature]
            right_summary = summaries[right]["features"][feature]
            if left_summary is None or right_summary is None:
                continue
            left_median = float(left_summary["median"])
            right_median = float(right_summary["median"])
            feature_comparisons[feature] = {
                "left_session": left,
                "right_session": right,
                "median_difference_left_minus_right": left_median - right_median,
                "median_ratio_left_over_right": left_median / right_median if right_median != 0 else None,
                "direction": _direction(left_median, right_median, left, right),
            }

        month_buckets[month] = {
            "eligible": eligible,
            "minimum_pair_n": minimum_pair_n,
            "counts": counts,
            "session_summaries": summaries,
            "comparison": feature_comparisons,
        }

    reference = spec["follow_up_design"]["base_observed_direction_reference"]
    persistence: dict[str, Any] = {}
    for feature in directional_features:
        expected_direction = str(reference[feature])
        matching = 0
        observed = 0
        for month in eligible_months:
            comparison_record = month_buckets[month]["comparison"].get(feature)
            if not isinstance(comparison_record, dict):
                continue
            observed += 1
            if comparison_record.get("direction") == expected_direction:
                matching += 1
        persistence[feature] = {
            "base_direction": expected_direction,
            "eligible_bucket_count": observed,
            "matching_direction_bucket_count": matching,
            "matching_direction_fraction": matching / observed if observed else None,
        }

    return {
        "bucket_basis": temporal["bucket_basis"],
        "minimum_pair_n_per_bucket": minimum_pair_n,
        "eligible_bucket_count": len(eligible_months),
        "eligible_buckets": eligible_months,
        "month_buckets": month_buckets,
        "directional_persistence": persistence,
        "statistical_significance_test": "none",
        "regime_labels": "none",
    }


def run_named_session_tpo_temporal_robustness(
    csv_path: str | Path,
    *,
    spec_path: str | Path = "quant/studies/XAUUSD_NAMED_SESSION_TPO_TEMPORAL_ROBUSTNESS_V1.yaml",
    repo_root: str | Path = ".",
) -> dict[str, Any]:
    root = Path(repo_root)
    spec_file = Path(spec_path)
    if not spec_file.is_absolute():
        spec_file = root / spec_file

    spec_validation = validate_study_spec(spec_file, root)
    if spec_validation.errors:
        raise ValueError("invalid robustness study specification: " + "; ".join(spec_validation.errors))
    spec = _load_yaml(spec_file)

    follow_up = spec.get("follow_up_design", {})
    base_result_path = root / str(follow_up.get("base_result_path", ""))
    base_validation = validate_study_result(base_result_path, root)
    if base_validation.errors:
        raise ValueError("invalid base study result: " + "; ".join(base_validation.errors))

    base = run_named_session_tpo_study(
        csv_path,
        spec_path=spec_file,
        repo_root=root,
        include_rows=True,
    )
    feature_rows = base.pop("feature_rows")
    temporal = summarize_temporal_feature_rows(feature_rows, spec)

    return {
        "study_id": spec["study_id"],
        "spec_status": spec["status"],
        "study_type": spec["study_type"],
        "declared_follow_up": True,
        "base_study_id": follow_up["base_study_id"],
        "base_result_path": follow_up["base_result_path"],
        "dataset_id": spec["data"]["dataset_id"],
        "input_csv": str(Path(csv_path)),
        "timeframe": spec["data"]["timeframe"],
        "cutoff_utc": spec["data"]["cutoff_utc"],
        "session_policy_id": spec["session_context"]["policy_id"],
        "selection_policy": dict(spec["session_context"]["selection"]),
        "operational_rule_id": spec["operational_input"]["rule_id"],
        "price_increment": str(spec["operational_input"]["price_increment"]),
        "aggregate_reference": base,
        "temporal_robustness": temporal,
        "interpretation_boundaries": dict(spec["interpretation_boundaries"]),
    }
