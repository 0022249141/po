from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


ALLOWED_CONCEPT_STATES = (
    "source_indexed",
    "source_noted",
    "defined",
    "operational_candidate",
    "operational",
    "backtest_ready",
    "validated",
    "rejected_or_unresolved",
)

STATE_RANK = {state: index for index, state in enumerate(ALLOWED_CONCEPT_STATES)}
STATE_RANK["rejected_or_unresolved"] = -1


@dataclass(frozen=True)
class ConceptValidationResult:
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


def _source_ids(registry: dict[str, Any]) -> set[str]:
    return {
        str(item["id"])
        for item in registry.get("sources", [])
        if isinstance(item, dict) and item.get("id")
    }


def validate_concept_registry(repo_root: str | Path = ".") -> ConceptValidationResult:
    root = Path(repo_root)
    concept_path = root / "knowledge" / "CONCEPT_REGISTRY.yaml"
    source_path = root / "config" / "source-registry.yaml"
    framework_path = root / "knowledge" / "FRAMEWORK_INGESTION_STATUS.yaml"

    errors: list[str] = []
    warnings: list[str] = []

    for path in (concept_path, source_path, framework_path):
        if not path.exists():
            errors.append(f"missing: {path}")
    if errors:
        return ConceptValidationResult(errors, warnings)

    try:
        concepts_doc = _load_yaml(concept_path)
        source_doc = _load_yaml(source_path)
        framework_doc = _load_yaml(framework_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return ConceptValidationResult([str(exc)], warnings)

    known_sources = _source_ids(source_doc)
    frameworks = framework_doc.get("frameworks", {})
    concepts = concepts_doc.get("concepts")
    if not isinstance(concepts, dict) or not concepts:
        return ConceptValidationResult(["concepts must be a non-empty mapping"], warnings)

    for concept_id, record in concepts.items():
        if not isinstance(record, dict):
            errors.append(f"{concept_id}: concept record must be a mapping")
            continue

        framework = record.get("framework")
        if framework not in frameworks:
            errors.append(f"{concept_id}: unknown framework {framework!r}")
            continue

        state = record.get("state")
        if state not in ALLOWED_CONCEPT_STATES:
            errors.append(f"{concept_id}: unsupported state {state!r}")
            continue

        ids = record.get("source_ids")
        if not isinstance(ids, list) or not ids:
            errors.append(f"{concept_id}: source_ids must be a non-empty list")
            continue

        framework_source_ids = set(frameworks[framework].get("source_ids", []))
        for source_id in ids:
            if source_id not in known_sources:
                errors.append(f"{concept_id}: unknown source_id {source_id}")
            elif source_id not in framework_source_ids:
                errors.append(
                    f"{concept_id}: source_id {source_id} is not registered under framework {framework}"
                )

        rank = STATE_RANK[state]
        evidence_path = record.get("evidence_path")
        if rank >= STATE_RANK["source_noted"]:
            if not evidence_path:
                errors.append(f"{concept_id}: {state} requires evidence_path")
            else:
                evidence_file = root / str(evidence_path)
                if not evidence_file.exists():
                    errors.append(f"{concept_id}: missing evidence_path {evidence_path}")

        definition_path = record.get("definition_path")
        if rank >= STATE_RANK["defined"]:
            if not definition_path:
                errors.append(f"{concept_id}: {state} requires definition_path")
            else:
                definition_file = root / str(definition_path)
                if not definition_file.exists():
                    errors.append(f"{concept_id}: missing definition_path {definition_path}")
                else:
                    text = definition_file.read_text(encoding="utf-8")
                    if str(concept_id) not in text:
                        errors.append(
                            f"{concept_id}: definition artifact does not mention concept id"
                        )

        if rank >= STATE_RANK["operational"] and not record.get("operational_rule_path"):
            errors.append(f"{concept_id}: {state} requires operational_rule_path")

        if rank >= STATE_RANK["backtest_ready"] and not record.get("quant_spec_path"):
            errors.append(f"{concept_id}: {state} requires quant_spec_path")

    rules = concepts_doc.get("rules", {})
    if not isinstance(rules, dict) or rules.get("no_cross_framework_definition_substitution") is not True:
        errors.append("concept registry must enforce no_cross_framework_definition_substitution")

    return ConceptValidationResult(errors, warnings)


def format_result(result: ConceptValidationResult) -> dict[str, object]:
    return {
        "status": result.status,
        "errors": result.errors,
        "warnings": result.warnings,
    }
