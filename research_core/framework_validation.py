from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml


ALLOWED_FRAMEWORK_STATES = {
    "source_indexed",
    "source_verified_partial",
    "defined_partial",
    "operational_candidate_partial",
    "operational_partial",
    "backtest_ready_partial",
    "validated_partial",
    "rejected_or_unresolved",
}


@dataclass(frozen=True)
class ValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def status(self) -> str:
        return "pass" if not self.errors else "fail"


def _load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def _registry_source_ids(registry: dict) -> set[str]:
    return {
        str(item.get("id"))
        for item in registry.get("sources", [])
        if isinstance(item, dict) and item.get("id")
    }


def validate_framework_ingestion(repo_root: str | Path = ".") -> ValidationResult:
    root = Path(repo_root)
    status_path = root / "knowledge" / "FRAMEWORK_INGESTION_STATUS.yaml"
    registry_path = root / "config" / "source-registry.yaml"

    errors: list[str] = []
    warnings: list[str] = []

    if not status_path.exists():
        return ValidationResult([f"missing: {status_path}"], warnings)
    if not registry_path.exists():
        return ValidationResult([f"missing: {registry_path}"], warnings)

    try:
        status_doc = _load_yaml(status_path)
        registry_doc = _load_yaml(registry_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return ValidationResult([str(exc)], warnings)

    source_ids = _registry_source_ids(registry_doc)
    frameworks = status_doc.get("frameworks")
    if not isinstance(frameworks, dict) or not frameworks:
        errors.append("frameworks must be a non-empty mapping")
        return ValidationResult(errors, warnings)

    for framework_name, framework in frameworks.items():
        if not isinstance(framework, dict):
            errors.append(f"{framework_name}: framework record must be a mapping")
            continue

        rel_path = framework.get("path")
        if not isinstance(rel_path, str) or not rel_path.strip():
            errors.append(f"{framework_name}: missing path")
            continue

        framework_dir = root / rel_path
        if not framework_dir.exists():
            errors.append(f"{framework_name}: missing framework path {rel_path}")

        state = framework.get("status")
        if state not in ALLOWED_FRAMEWORK_STATES:
            errors.append(f"{framework_name}: unsupported status {state!r}")

        ids = framework.get("source_ids")
        if not isinstance(ids, list) or not ids:
            errors.append(f"{framework_name}: source_ids must be a non-empty list")
        else:
            unknown = [source_id for source_id in ids if source_id not in source_ids]
            for source_id in unknown:
                errors.append(f"{framework_name}: unknown source_id {source_id}")

        verified = framework.get("verified_artifacts", [])
        if state == "source_verified_partial" and not verified:
            errors.append(f"{framework_name}: source_verified_partial requires verified_artifacts")

        if verified:
            if not isinstance(verified, list):
                errors.append(f"{framework_name}: verified_artifacts must be a list")
            else:
                for artifact in verified:
                    artifact_path = framework_dir / str(artifact)
                    if not artifact_path.exists():
                        errors.append(
                            f"{framework_name}: verified artifact missing: {artifact_path.relative_to(root)}"
                        )

        if framework.get("independent_definition_required") is not True:
            warnings.append(f"{framework_name}: independent_definition_required is not true")

    if not status_doc.get("promotion_rule"):
        errors.append("missing promotion_rule")

    return ValidationResult(errors, warnings)


def format_result(result: ValidationResult) -> dict[str, object]:
    return {
        "status": result.status,
        "errors": result.errors,
        "warnings": result.warnings,
    }
