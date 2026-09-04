from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


STATUS_VALUES = {"unresolved", "candidate", "verified"}
EVIDENCE_TYPES = {
    "direct_source_metadata",
    "broker_documentation",
    "terminal_observation",
    "controlled_crosscheck",
    "statistical_inference",
}
NON_STATISTICAL_EVIDENCE = EVIDENCE_TYPES - {"statistical_inference"}


@dataclass(frozen=True)
class TimebaseValidationResult:
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


def validate_timebase_document(doc: dict[str, Any], repo_root: str | Path | None = None) -> TimebaseValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    datasets = doc.get("datasets")
    if not isinstance(datasets, dict) or not datasets:
        return TimebaseValidationResult(["datasets must be a non-empty mapping"], warnings)

    for dataset_id, record in datasets.items():
        if not isinstance(record, dict):
            errors.append(f"{dataset_id}: record must be a mapping")
            continue

        for field in (
            "source_id",
            "status",
            "source_timestamp_semantics",
            "named_session_use_allowed",
            "evidence",
            "blockers",
        ):
            if field not in record:
                errors.append(f"{dataset_id}: missing required field {field}")

        status = record.get("status")
        if status not in STATUS_VALUES:
            errors.append(f"{dataset_id}: invalid status {status!r}")
            continue

        named_sessions = record.get("named_session_use_allowed")
        if not isinstance(named_sessions, bool):
            errors.append(f"{dataset_id}: named_session_use_allowed must be boolean")
        elif named_sessions and status != "verified":
            errors.append(f"{dataset_id}: named session use requires verified timebase")

        evidence = record.get("evidence", [])
        if not isinstance(evidence, list):
            errors.append(f"{dataset_id}: evidence must be a list")
            evidence = []

        evidence_types: list[str] = []
        for index, item in enumerate(evidence, start=1):
            if not isinstance(item, dict):
                errors.append(f"{dataset_id}: evidence #{index} must be a mapping")
                continue
            evidence_type = item.get("type")
            if evidence_type not in EVIDENCE_TYPES:
                errors.append(f"{dataset_id}: evidence #{index} has invalid type {evidence_type!r}")
                continue
            evidence_types.append(str(evidence_type))
            if not str(item.get("provenance", "")).strip():
                errors.append(f"{dataset_id}: evidence #{index} requires provenance")

        blockers = record.get("blockers", [])
        if not isinstance(blockers, list):
            errors.append(f"{dataset_id}: blockers must be a list")
            blockers = []

        if status == "unresolved":
            if named_sessions is True:
                errors.append(f"{dataset_id}: unresolved timebase cannot authorize named sessions")
            if not record.get("neutral_policy"):
                warnings.append(f"{dataset_id}: unresolved timebase has no neutral_policy")
            if not blockers:
                warnings.append(f"{dataset_id}: unresolved timebase should state blockers")

        if status in {"candidate", "verified"} and not evidence:
            errors.append(f"{dataset_id}: {status} status requires evidence")

        if status == "verified":
            for field in ("source_timezone", "dst_policy", "broker_feed_identity"):
                if not str(record.get(field, "")).strip():
                    errors.append(f"{dataset_id}: verified status requires {field}")
            if not any(item in NON_STATISTICAL_EVIDENCE for item in evidence_types):
                errors.append(f"{dataset_id}: verified status requires non-statistical timebase evidence")
            if blockers:
                errors.append(f"{dataset_id}: verified status cannot retain unresolved blockers")

        if repo_root is not None:
            root = Path(repo_root)
            for path_field in ("bundle_manifest", "qualification_report"):
                value = record.get(path_field)
                if value and not (root / str(value)).exists():
                    errors.append(f"{dataset_id}: missing {path_field}: {value}")

    rules = doc.get("rules")
    if not isinstance(rules, dict):
        errors.append("timebase registry missing rules mapping")
    else:
        required_true = {
            "verified_requires_non_statistical_evidence",
            "statistical_inference_alone_cannot_verify",
            "named_session_use_requires_verified",
            "no_timezone_inference_from_filename",
            "no_timezone_inference_from_gap_pattern_alone",
        }
        for key in required_true:
            if rules.get(key) is not True:
                errors.append(f"timebase rule {key} must be true")

    return TimebaseValidationResult(errors, warnings)


def validate_timebase_registry(repo_root: str | Path = ".") -> TimebaseValidationResult:
    root = Path(repo_root)
    path = root / "config" / "timebase" / "XAUUSD_o.yaml"
    if not path.exists():
        return TimebaseValidationResult([f"missing: {path}"], [])
    try:
        doc = _load_yaml(path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return TimebaseValidationResult([str(exc)], [])
    return validate_timebase_document(doc, repo_root=root)


def format_result(result: TimebaseValidationResult) -> dict[str, object]:
    return {"status": result.status, "errors": result.errors, "warnings": result.warnings}
