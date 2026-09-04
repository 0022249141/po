from __future__ import annotations

from pathlib import Path
from typing import Any
import json


REQUIRED_DIRECTIONAL_FEATURES = ("range_ticks", "occupancy_events")


def _load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("regime result must be a JSON object")
    return payload


def summarize_regime_result(payload: dict[str, Any]) -> dict[str, Any]:
    study_id = payload.get("study_id")
    regime = payload.get("regime_robustness")
    if not study_id:
        raise ValueError("missing study_id")
    if not isinstance(regime, dict):
        raise ValueError("missing regime_robustness mapping")

    buckets = regime.get("regime_buckets")
    persistence = regime.get("directional_persistence")
    if not isinstance(buckets, dict):
        raise ValueError("missing regime_buckets mapping")
    if not isinstance(persistence, dict):
        raise ValueError("missing directional_persistence mapping")

    bucket_summary: dict[str, Any] = {}
    for label in ("low", "normal", "high"):
        record = buckets.get(label)
        if not isinstance(record, dict):
            raise ValueError(f"missing regime bucket: {label}")
        counts = record.get("counts")
        comparison = record.get("comparison")
        if not isinstance(counts, dict):
            raise ValueError(f"{label}: counts must be a mapping")
        if not isinstance(comparison, dict):
            raise ValueError(f"{label}: comparison must be a mapping")

        directions: dict[str, str | None] = {}
        for feature in REQUIRED_DIRECTIONAL_FEATURES:
            feature_record = comparison.get(feature)
            directions[feature] = (
                str(feature_record.get("direction"))
                if isinstance(feature_record, dict) and feature_record.get("direction") is not None
                else None
            )

        bucket_summary[label] = {
            "eligible": bool(record.get("eligible")),
            "london_n": int(counts.get("london", 0)),
            "new_york_n": int(counts.get("new_york", 0)),
            "directions": directions,
        }

    persistence_summary: dict[str, Any] = {}
    for feature in REQUIRED_DIRECTIONAL_FEATURES:
        record = persistence.get(feature)
        if not isinstance(record, dict):
            raise ValueError(f"missing directional persistence: {feature}")
        persistence_summary[feature] = {
            "base_direction": record.get("base_direction"),
            "eligible_regime_count": int(record.get("eligible_regime_count", 0)),
            "matching_direction_regime_count": int(record.get("matching_direction_regime_count", 0)),
            "matching_direction_fraction": record.get("matching_direction_fraction"),
        }

    return {
        "study_id": study_id,
        "regime_id": regime.get("regime_id"),
        "paired_date_count": int(regime.get("paired_date_count", 0)),
        "warmup_excluded_paired_dates": int(regime.get("warmup_excluded_paired_dates", 0)),
        "labeled_paired_date_count": int(regime.get("labeled_paired_date_count", 0)),
        "eligible_regime_count": int(regime.get("eligible_regime_count", 0)),
        "eligible_regimes": list(regime.get("eligible_regimes") or []),
        "buckets": bucket_summary,
        "directional_persistence": persistence_summary,
        "statistical_significance_test": regime.get("statistical_significance_test"),
    }


def summarize_regime_result_file(path: str | Path) -> dict[str, Any]:
    return summarize_regime_result(_load_json(path))
