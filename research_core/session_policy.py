from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml


UTC = timezone.utc


@dataclass(frozen=True)
class SessionDefinition:
    session_id: str
    display_name: str
    timezone_name: str
    start_local: time
    end_local: time
    weekdays: tuple[int, ...]

    @property
    def crosses_midnight(self) -> bool:
        return self.end_local <= self.start_local


@dataclass(frozen=True)
class SessionPolicyValidationResult:
    errors: list[str]
    warnings: list[str]

    @property
    def status(self) -> str:
        return "pass" if not self.errors else "fail"


def _parse_hhmm(value: Any, field_name: str) -> time:
    text = str(value).strip()
    try:
        hh, mm = text.split(":", 1)
        parsed = time(hour=int(hh), minute=int(mm))
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{field_name} must be HH:MM") from exc
    if f"{parsed.hour:02d}:{parsed.minute:02d}" != text:
        raise ValueError(f"{field_name} must be zero-padded HH:MM")
    return parsed


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data


def validate_session_policy_document(doc: dict[str, Any]) -> SessionPolicyValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    for field in ("version", "policy_id", "status", "input_timebase_requirement", "sessions", "rules"):
        if field not in doc:
            errors.append(f"missing required field: {field}")

    if doc.get("input_timebase_requirement") != "verified_utc":
        errors.append("input_timebase_requirement must be verified_utc")

    sessions = doc.get("sessions")
    if not isinstance(sessions, dict) or not sessions:
        errors.append("sessions must be a non-empty mapping")
        sessions = {}

    for session_id, record in sessions.items():
        if not isinstance(record, dict):
            errors.append(f"{session_id}: session record must be a mapping")
            continue
        for field in ("display_name", "timezone", "start_local", "end_local", "weekdays"):
            if field not in record:
                errors.append(f"{session_id}: missing {field}")

        timezone_name = str(record.get("timezone", "")).strip()
        if timezone_name:
            try:
                ZoneInfo(timezone_name)
            except ZoneInfoNotFoundError:
                errors.append(f"{session_id}: IANA timezone not available: {timezone_name}")

        for field in ("start_local", "end_local"):
            try:
                _parse_hhmm(record.get(field, ""), f"{session_id}.{field}")
            except ValueError as exc:
                errors.append(str(exc))

        weekdays = record.get("weekdays")
        if not isinstance(weekdays, list) or not weekdays:
            errors.append(f"{session_id}: weekdays must be a non-empty list")
        elif any(not isinstance(day, int) or day < 0 or day > 6 for day in weekdays):
            errors.append(f"{session_id}: weekdays must contain integers 0..6")
        elif len(set(weekdays)) != len(weekdays):
            errors.append(f"{session_id}: weekdays must not contain duplicates")

    rules = doc.get("rules")
    required_true = {
        "iana_timezone_required",
        "dst_from_timezone_database",
        "fixed_utc_offsets_prohibited",
        "verified_utc_input_required",
        "start_inclusive",
        "end_exclusive",
        "holiday_inference_prohibited",
        "missing_market_data_does_not_shift_session_boundaries",
        "not_ict_kill_zones",
    }
    if not isinstance(rules, dict):
        errors.append("rules must be a mapping")
    else:
        for key in required_true:
            if rules.get(key) is not True:
                errors.append(f"session policy rule {key} must be true")

    source_boundary = doc.get("source_boundary")
    if not isinstance(source_boundary, dict):
        warnings.append("source_boundary mapping is recommended")
    else:
        refs = source_boundary.get("references")
        if not isinstance(refs, list) or not refs:
            warnings.append("source_boundary.references should be non-empty")

    return SessionPolicyValidationResult(errors, warnings)


class NamedSessionPolicy:
    def __init__(self, definitions: dict[str, SessionDefinition], policy_id: str):
        if not definitions:
            raise ValueError("at least one session definition is required")
        self.definitions = definitions
        self.policy_id = policy_id

    @classmethod
    def from_document(cls, doc: dict[str, Any]) -> "NamedSessionPolicy":
        result = validate_session_policy_document(doc)
        if result.errors:
            raise ValueError("invalid session policy: " + "; ".join(result.errors))

        definitions: dict[str, SessionDefinition] = {}
        for session_id, record in doc["sessions"].items():
            definitions[str(session_id)] = SessionDefinition(
                session_id=str(session_id),
                display_name=str(record["display_name"]),
                timezone_name=str(record["timezone"]),
                start_local=_parse_hhmm(record["start_local"], f"{session_id}.start_local"),
                end_local=_parse_hhmm(record["end_local"], f"{session_id}.end_local"),
                weekdays=tuple(int(day) for day in record["weekdays"]),
            )
        return cls(definitions, str(doc["policy_id"]))

    @classmethod
    def from_yaml(cls, path: str | Path) -> "NamedSessionPolicy":
        return cls.from_document(_load_yaml(Path(path)))

    def _definition(self, session_id: str) -> SessionDefinition:
        try:
            return self.definitions[session_id]
        except KeyError as exc:
            raise KeyError(f"unknown session_id: {session_id}") from exc

    def bounds_utc(self, session_id: str, local_start_date: date) -> tuple[datetime, datetime]:
        definition = self._definition(session_id)
        if local_start_date.weekday() not in definition.weekdays:
            raise ValueError(f"{session_id} is not active on local weekday {local_start_date.weekday()}")

        zone = ZoneInfo(definition.timezone_name)
        start = datetime.combine(local_start_date, definition.start_local, tzinfo=zone)
        end_date = local_start_date + timedelta(days=1) if definition.crosses_midnight else local_start_date
        end = datetime.combine(end_date, definition.end_local, tzinfo=zone)
        return start.astimezone(UTC), end.astimezone(UTC)

    def contains(self, session_id: str, timestamp_utc: datetime) -> bool:
        if timestamp_utc.tzinfo is None or timestamp_utc.utcoffset() is None:
            raise ValueError("timestamp_utc must be timezone-aware")
        instant = timestamp_utc.astimezone(UTC)
        definition = self._definition(session_id)
        local_date = instant.astimezone(ZoneInfo(definition.timezone_name)).date()

        for candidate_date in (local_date, local_date - timedelta(days=1)):
            if candidate_date.weekday() not in definition.weekdays:
                continue
            start, end = self.bounds_utc(session_id, candidate_date)
            if start <= instant < end:
                return True
        return False

    def classify(self, timestamp_utc: datetime) -> list[str]:
        return [session_id for session_id in self.definitions if self.contains(session_id, timestamp_utc)]

    def session_instance_id(self, session_id: str, timestamp_utc: datetime) -> str | None:
        if timestamp_utc.tzinfo is None or timestamp_utc.utcoffset() is None:
            raise ValueError("timestamp_utc must be timezone-aware")
        instant = timestamp_utc.astimezone(UTC)
        definition = self._definition(session_id)
        local_date = instant.astimezone(ZoneInfo(definition.timezone_name)).date()
        for candidate_date in (local_date, local_date - timedelta(days=1)):
            if candidate_date.weekday() not in definition.weekdays:
                continue
            start, end = self.bounds_utc(session_id, candidate_date)
            if start <= instant < end:
                return f"{session_id}:{candidate_date.isoformat()}"
        return None


def validate_session_policy_file(path: str | Path) -> SessionPolicyValidationResult:
    try:
        doc = _load_yaml(Path(path))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return SessionPolicyValidationResult([str(exc)], [])
    return validate_session_policy_document(doc)


def format_validation_result(result: SessionPolicyValidationResult) -> dict[str, object]:
    return {"status": result.status, "errors": result.errors, "warnings": result.warnings}
