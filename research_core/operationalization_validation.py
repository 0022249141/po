from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


CONCEPT_STATES = {
    "source_indexed",
    "source_noted",
    "defined",
    "operational_candidate",
    "operational",
    "backtest_ready",
    "validated",
    "rejected_or_unresolved",
}

READINESS_STATES = {"blocked", "candidate", "operational", "backtest_ready"}

MACHINE_FIELDS = {
    "instrument_scope",
    "input_data",
    "timeframe_or_event_clock",
    "lookback",
    "reference_set",
    "state_variables",
    "trigger",
    "confirmation",
    "invalidation",
    "forming_bar_policy",
    "timezone_or_session_dependency",
    "missing_data_policy",
    "tie_and_edge_case_policy",
}


@dataclass(frozen=True)
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def status(self) -> str:
        return "pass" if not self.errors else "fail"


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def validate_operationalization(repo_root: str | Path = ".") -> ValidationResult:
    root = Path(repo_root)
    op_path = root / "knowledge" / "OPERATIONALIZATION_REGISTRY.yaml"
    concept_path = root / "knowledge" / "CONCEPT_REGISTRY.yaml"

    errors: list[str] = []
    warnings: list[str] = []

    if not op_path.exists():
        return ValidationResult([f"missing: {op_path}"], warnings)
    if not concept_path.exists():
        return ValidationResult([f"missing: {concept_path}"], warnings)

    try:
        op_doc = _load_yaml(op_path)
        concept_doc = _load_yaml(concept_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return ValidationResult([str(exc)], warnings)

    concepts = concept_doc.get("concepts")
    assessments = op_doc.get("assessments")
    if not isinstance(concepts, dict) or not concepts:
        errors.append("concept registry must contain a non-empty concepts mapping")
        return ValidationResult(errors, warnings)
    if not isinstance(assessments, dict) or not assessments:
        errors.append("operationalization registry must contain a non-empty assessments mapping")
        return ValidationResult(errors, warnings)

    for concept_id, record in assessments.items():
        if concept_id not in concepts:
            errors.append(f"{concept_id}: not present in CONCEPT_REGISTRY.yaml")
            continue
        if not isinstance(record, dict):
            errors.append(f"{concept_id}: assessment must be a mapping")
            continue

        concept = concepts[concept_id]
        if not isinstance(concept, dict):
            errors.append(f"{concept_id}: concept registry record must be a mapping")
            continue

        source_state = concept.get("state")
        if source_state not in CONCEPT_STATES:
            errors.append(f"{concept_id}: invalid concept state {source_state!r}")

        declared_state = record.get("concept_state")
        if declared_state != source_state:
            errors.append(
                f"{concept_id}: concept_state mismatch: registry={source_state!r}, operationalization={declared_state!r}"
            )

        if source_state not in {"defined", "operational_candidate", "operational", "backtest_ready", "validated"}:
            errors.append(f"{concept_id}: operationalization assessment requires a defined-or-higher concept")

        readiness = record.get("readiness")
        if readiness not in READINESS_STATES:
            errors.append(f"{concept_id}: unsupported readiness {readiness!r}")

        machine_ready = record.get("machine_ready")
        if not isinstance(machine_ready, bool):
            errors.append(f"{concept_id}: machine_ready must be boolean")
            continue

        blockers = record.get("blockers", [])
        if readiness == "blocked":
            if machine_ready:
                errors.append(f"{concept_id}: blocked assessment cannot be machine_ready")
            if not isinstance(blockers, list) or not blockers:
                errors.append(f"{concept_id}: blocked assessment requires explicit blockers")
        elif blockers:
            warnings.append(f"{concept_id}: non-blocked assessment still lists blockers")

        if machine_ready:
            missing = [field for field in sorted(MACHINE_FIELDS) if not record.get(field)]
            for field in missing:
                errors.append(f"{concept_id}: machine_ready missing mandatory field {field}")

            spec_path = record.get("candidate_spec_path")
            if not isinstance(spec_path, str) or not spec_path.strip():
                errors.append(f"{concept_id}: machine_ready requires candidate_spec_path")
            else:
                path = root / spec_path
                if not path.exists():
                    errors.append(f"{concept_id}: candidate spec missing: {spec_path}")

        target_role = str(record.get("target_role", ""))
        if target_role == "theoretical_feature_candidate" and machine_ready and not record.get("measurable_proxy"):
            errors.append(f"{concept_id}: theoretical concept requires measurable_proxy before machine readiness")

    rules = op_doc.get("rules")
    if not isinstance(rules, dict):
        errors.append("operationalization registry missing rules mapping")
    else:
        required_truths = {
            "machine_ready_requires_all_mandatory_fields",
            "blocked_requires_explicit_blockers",
            "theoretical_concepts_require_measurable_proxy",
            "no_ohlc_only_dealer_inventory_claims",
            "no_hindsight_or_future_information",
        }
        for key in required_truths:
            if rules.get(key) is not True:
                errors.append(f"operationalization rule {key} must be true")

    return ValidationResult(errors, warnings)


def format_result(result: ValidationResult) -> dict[str, object]:
    return {"status": result.status, "errors": result.errors, "warnings": result.warnings}
