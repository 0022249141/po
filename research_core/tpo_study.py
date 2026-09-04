from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import math

import yaml

from .named_session_dataset import COMPLETE_ONLY, SessionSelectionPolicy, build_named_session_tpo
from .session_policy import NamedSessionPolicy
from .study_spec_validation import validate_study_spec


@dataclass(frozen=True)
class StudyFeatureRow:
    session_id: str
    session_instance_id: str
    range_ticks: float
    occupied_bins: float
    occupancy_events: float
    mean_bin_occupancy: float
    bars_seen: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "session_instance_id": self.session_instance_id,
            "range_ticks": self.range_ticks,
            "occupied_bins": self.occupied_bins,
            "occupancy_events": self.occupancy_events,
            "mean_bin_occupancy": self.mean_bin_occupancy,
            "bars_seen": self.bars_seen,
        }


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _quantile_linear(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("quantile requires at least one value")
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be within [0, 1]")
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


def _feature_row(instance: dict[str, Any]) -> StudyFeatureRow:
    profile = instance.get("profile")
    if not isinstance(profile, dict):
        raise ValueError(f"selected session has no profile: {instance.get('session_instance_id')}")
    bins = profile.get("bins")
    if not isinstance(bins, dict) or not bins:
        raise ValueError(f"selected session has no occupied bins: {instance.get('session_instance_id')}")
    low_tick = profile.get("observed_session_low_tick")
    high_tick = profile.get("observed_session_high_tick")
    if low_tick is None or high_tick is None:
        raise ValueError(f"selected session has no observed range: {instance.get('session_instance_id')}")
    occupancy_events = sum(int(value) for value in bins.values())
    occupied_bins = len(bins)
    return StudyFeatureRow(
        session_id=str(instance["session_id"]),
        session_instance_id=str(instance["session_instance_id"]),
        range_ticks=float(int(high_tick) - int(low_tick)),
        occupied_bins=float(occupied_bins),
        occupancy_events=float(occupancy_events),
        mean_bin_occupancy=float(occupancy_events / occupied_bins),
        bars_seen=float(profile.get("bars_seen", 0)),
    )


def run_named_session_tpo_study(
    csv_path: str | Path,
    *,
    spec_path: str | Path,
    repo_root: str | Path = ".",
    include_rows: bool = False,
) -> dict[str, Any]:
    root = Path(repo_root)
    spec_file = Path(spec_path)
    if not spec_file.is_absolute():
        spec_file = root / spec_file

    validation = validate_study_spec(spec_file, root)
    if validation.errors:
        raise ValueError("invalid study specification: " + "; ".join(validation.errors))
    spec = _load_yaml(spec_file)

    session_doc = spec["session_context"]
    policy = NamedSessionPolicy.from_yaml(root / session_doc["policy_path"])
    selection = SessionSelectionPolicy(
        completeness_mode=COMPLETE_ONLY,
        exclude_coverage_edges=True,
    )
    data = spec["data"]
    op = spec["operational_input"]
    requested_features = list(spec["features"])
    session_ids = list(session_doc["sessions"])

    rows_by_session: dict[str, list[StudyFeatureRow]] = {}
    adapter_counts: dict[str, dict[str, int]] = {}

    # Process one session at a time so large profile-bin payloads are released before the next
    # session is evaluated. The raw market-data file remains external and is never written to Git.
    for session_id in session_ids:
        payload = build_named_session_tpo(
            csv_path,
            timeframe=str(data["timeframe"]),
            cutoff=str(data["cutoff_utc"]),
            price_increment=str(op["price_increment"]),
            session_policy=policy,
            session_ids=[session_id],
            selection_policy=selection,
        )
        rows = [_feature_row(instance) for instance in payload["instances"]]
        rows_by_session[session_id] = rows
        adapter_counts[session_id] = dict(payload["counts"])

    summaries: dict[str, Any] = {}
    for session_id, rows in rows_by_session.items():
        session_summary: dict[str, Any] = {"n": len(rows), "features": {}}
        for feature in requested_features:
            values = [float(getattr(row, feature)) for row in rows]
            session_summary["features"][feature] = _summarize(values) if values else None
        summaries[session_id] = session_summary

    sample_policy = spec["sample_policy"]
    minimum_primary_n = int(sample_policy["minimum_primary_n"])
    primary_sessions = list(sample_policy["primary_sessions"])
    primary_eligibility = {
        session_id: len(rows_by_session.get(session_id, [])) >= minimum_primary_n
        for session_id in primary_sessions
    }

    comparisons: dict[str, Any] = {
        "status": "eligible" if all(primary_eligibility.values()) else "underpowered",
        "minimum_primary_n": minimum_primary_n,
        "primary_eligibility": primary_eligibility,
        "statistical_significance_test": "none",
        "features": {},
    }
    comparison = spec["comparison_policy"]
    pair = list(comparison.get("primary_pair") or primary_sessions[:2])
    if len(pair) == 2 and all(session in summaries for session in pair):
        left, right = pair
        for feature in requested_features:
            left_summary = summaries[left]["features"][feature]
            right_summary = summaries[right]["features"][feature]
            if left_summary is None or right_summary is None:
                continue
            left_median = float(left_summary["median"])
            right_median = float(right_summary["median"])
            comparisons["features"][feature] = {
                "left_session": left,
                "right_session": right,
                "median_difference_left_minus_right": left_median - right_median,
                "median_ratio_left_over_right": (
                    left_median / right_median if right_median != 0 else None
                ),
            }

    result: dict[str, Any] = {
        "study_id": spec["study_id"],
        "spec_status": spec["status"],
        "study_type": spec["study_type"],
        "dataset_id": data["dataset_id"],
        "dataset_manifest": data["dataset_manifest"],
        "input_csv": str(Path(csv_path)),
        "timeframe": data["timeframe"],
        "cutoff_utc": data["cutoff_utc"],
        "session_policy_id": session_doc["policy_id"],
        "selection_policy": {
            "completeness_mode": COMPLETE_ONLY,
            "exclude_coverage_edges": True,
        },
        "operational_rule_id": op["rule_id"],
        "price_increment": str(op["price_increment"]),
        "quantile_method": "linear interpolation at position (n-1)*p",
        "adapter_counts": adapter_counts,
        "session_summaries": summaries,
        "primary_comparison": comparisons,
        "interpretation_boundaries": dict(spec["interpretation_boundaries"]),
    }
    if include_rows:
        result["feature_rows"] = {
            session_id: [row.as_dict() for row in rows]
            for session_id, rows in rows_by_session.items()
        }
    return result
