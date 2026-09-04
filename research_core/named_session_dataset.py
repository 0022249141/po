from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from .data_validation import TIMEFRAME_SECONDS, _norm_row, extract_timestamp, read_csv_rows
from .session_policy import NamedSessionPolicy
from .tpo_profile import CLOSED, TPOBar, TPOProfileEngine


UTC = timezone.utc
COMPLETE_ONLY = "complete_only"
ALLOW_INCOMPLETE_WITH_FLAG = "allow_incomplete_with_flag"
COMPLETENESS_MODES = {COMPLETE_ONLY, ALLOW_INCOMPLETE_WITH_FLAG}


@dataclass(frozen=True)
class SessionSelectionPolicy:
    """Dataset-selection policy applied after deterministic session classification.

    Coverage-edge instances are excluded by default because a dataset start/cutoff can make an
    otherwise valid session appear incomplete. Completeness handling is independent: downstream
    research can either require full coverage or retain incomplete instances with an explicit flag.
    """

    completeness_mode: str = COMPLETE_ONLY
    exclude_coverage_edges: bool = True

    def __post_init__(self) -> None:
        if self.completeness_mode not in COMPLETENESS_MODES:
            raise ValueError(f"unsupported completeness_mode: {self.completeness_mode}")


@dataclass
class _Instance:
    session_id: str
    instance_id: str
    local_start_date: date
    start_utc: datetime
    end_utc: datetime
    expected_opens: list[datetime]
    observed_rows: list[tuple[datetime, dict[str, Any]]]
    coverage_edge: bool = False

    @property
    def observed_opens(self) -> set[datetime]:
        return {ts for ts, _ in self.observed_rows}

    @property
    def missing_opens(self) -> list[datetime]:
        observed = self.observed_opens
        return [ts for ts in self.expected_opens if ts not in observed]

    @property
    def complete(self) -> bool:
        return not self.coverage_edge and not self.missing_opens


def _decimal_field(row: dict[str, Any], name: str) -> Decimal:
    normalized = _norm_row(row)
    value = normalized.get(name)
    if value is None or str(value).strip() == "":
        raise ValueError(f"missing {name}")
    return Decimal(str(value).replace(",", "").strip())


def _parse_aware_utc(value: datetime | str, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return parsed.astimezone(UTC)


def _iter_local_dates(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _expected_opens(start: datetime, end: datetime, interval: timedelta) -> list[datetime]:
    if interval <= timedelta(0):
        raise ValueError("interval must be positive")
    result: list[datetime] = []
    current = start
    while current < end:
        result.append(current)
        current += interval
    if result and result[-1] >= end:
        raise AssertionError("session expected-open construction crossed end boundary")
    return result


def _collect_instances(
    csv_path: str | Path,
    *,
    timeframe: str,
    cutoff: datetime | str,
    policy: NamedSessionPolicy,
    session_ids: Iterable[str] | None,
) -> tuple[list[_Instance], dict[str, Any]]:
    tf = timeframe.upper()
    if tf not in TIMEFRAME_SECONDS:
        raise ValueError(f"unsupported timeframe: {timeframe}")
    interval = timedelta(seconds=TIMEFRAME_SECONDS[tf])
    cutoff_utc = _parse_aware_utc(cutoff, "cutoff")

    requested = list(session_ids) if session_ids is not None else list(policy.definitions)
    if not requested:
        raise ValueError("at least one session_id is required")
    for session_id in requested:
        if session_id not in policy.definitions:
            raise KeyError(f"unknown session_id: {session_id}")

    rows, csv_meta = read_csv_rows(csv_path)
    closed_rows: list[tuple[datetime, dict[str, Any]]] = []
    all_times: list[datetime] = []
    previous: datetime | None = None

    for raw in rows:
        ts = extract_timestamp(raw)
        if ts.tzinfo is None or ts.utcoffset() is None:
            raise ValueError("named-session adapter requires timezone-aware UTC input timestamps")
        ts_utc = ts.astimezone(UTC)
        if previous is not None and ts_utc <= previous:
            raise ValueError("input timestamps must be strictly increasing")
        previous = ts_utc
        all_times.append(ts_utc)
        if ts_utc + interval <= cutoff_utc:
            closed_rows.append((ts_utc, raw))

    if not all_times:
        raise ValueError("empty dataset")

    dataset_first = all_times[0]
    instances: dict[tuple[str, date], _Instance] = {}

    for session_id in requested:
        definition = policy.definitions[session_id]
        zone = ZoneInfo(definition.timezone_name)
        local_first = dataset_first.astimezone(zone).date() - timedelta(days=1)
        local_last = cutoff_utc.astimezone(zone).date() + timedelta(days=1)
        for local_date in _iter_local_dates(local_first, local_last):
            if local_date.weekday() not in definition.weekdays:
                continue
            start_utc, end_utc = policy.bounds_utc(session_id, local_date)
            if end_utc <= dataset_first or start_utc > cutoff_utc:
                continue
            key = (session_id, local_date)
            instances[key] = _Instance(
                session_id=session_id,
                instance_id=f"{session_id}:{local_date.isoformat()}",
                local_start_date=local_date,
                start_utc=start_utc,
                end_utc=end_utc,
                expected_opens=_expected_opens(start_utc, end_utc, interval),
                observed_rows=[],
                coverage_edge=start_utc < dataset_first or end_utc > cutoff_utc,
            )

    for ts_utc, raw in closed_rows:
        for session_id in requested:
            instance_id = policy.session_instance_id(session_id, ts_utc)
            if instance_id is None:
                continue
            local_date = date.fromisoformat(instance_id.split(":", 1)[1])
            instance = instances.get((session_id, local_date))
            if instance is not None:
                instance.observed_rows.append((ts_utc, raw))

    ordered = sorted(instances.values(), key=lambda item: (item.start_utc, item.session_id))
    meta = {
        "csv": csv_meta,
        "file": str(Path(csv_path)),
        "timeframe": tf,
        "cutoff_utc": cutoff_utc.isoformat(),
        "dataset_first_utc": dataset_first.isoformat(),
        "rows_total": len(rows),
        "closed_rows_at_cutoff": len(closed_rows),
    }
    return ordered, meta


def build_named_session_tpo(
    csv_path: str | Path,
    *,
    timeframe: str,
    cutoff: datetime | str,
    price_increment: Decimal | float | int | str,
    session_policy: NamedSessionPolicy,
    session_ids: Iterable[str] | None = None,
    selection_policy: SessionSelectionPolicy | None = None,
) -> dict[str, Any]:
    """Build descriptive TPO occupancy profiles for explicit named-session instances.

    The adapter requires timezone-aware canonical input. Session classification is delegated to a
    separately validated IANA/DST-aware policy. It never moves session boundaries around missing
    feed data and never interprets these research sessions as ICT kill zones.
    """

    selection = selection_policy or SessionSelectionPolicy()
    instances, input_meta = _collect_instances(
        csv_path,
        timeframe=timeframe,
        cutoff=cutoff,
        policy=session_policy,
        session_ids=session_ids,
    )

    output_instances: list[dict[str, Any]] = []
    excluded = {"coverage_edge": 0, "incomplete": 0}

    for instance in instances:
        missing = instance.missing_opens
        if selection.exclude_coverage_edges and instance.coverage_edge:
            excluded["coverage_edge"] += 1
            continue
        if selection.completeness_mode == COMPLETE_ONLY and not instance.complete:
            excluded["incomplete"] += 1
            continue

        engine = TPOProfileEngine(price_increment)
        if missing:
            engine.mark_incomplete("session_missing_expected_bars")

        previous: datetime | None = None
        for ts_utc, raw in sorted(instance.observed_rows, key=lambda item: item[0]):
            gap_before = previous is not None and ts_utc - previous > timedelta(seconds=TIMEFRAME_SECONDS[input_meta["timeframe"]])
            engine.update(
                TPOBar(
                    timestamp=ts_utc,
                    low=_decimal_field(raw, "low"),
                    high=_decimal_field(raw, "high"),
                    close_status=CLOSED,
                    session_id=instance.instance_id,
                    gap_before=gap_before,
                )
            )
            previous = ts_utc

        profile = engine.snapshot() if instance.observed_rows else None
        output_instances.append(
            {
                "session_id": instance.session_id,
                "session_instance_id": instance.instance_id,
                "local_start_date": instance.local_start_date.isoformat(),
                "start_utc": instance.start_utc.isoformat(),
                "end_utc": instance.end_utc.isoformat(),
                "expected_bars": len(instance.expected_opens),
                "observed_bars": len(instance.observed_rows),
                "missing_bars": len(missing),
                "missing_open_utc": [ts.isoformat() for ts in missing],
                "coverage_edge": instance.coverage_edge,
                "complete": instance.complete,
                "profile": profile,
            }
        )

    complete_count = sum(1 for item in output_instances if item["complete"])
    incomplete_count = len(output_instances) - complete_count
    return {
        "adapter": "named_session_tpo_v1",
        "session_policy_id": session_policy.policy_id,
        "selection_policy": {
            "completeness_mode": selection.completeness_mode,
            "exclude_coverage_edges": selection.exclude_coverage_edges,
        },
        "input": {
            **input_meta,
            "price_increment": str(Decimal(str(price_increment))),
            "timestamp_requirement": "timezone-aware canonical UTC",
        },
        "counts": {
            "candidate_instances": len(instances),
            "selected_instances": len(output_instances),
            "selected_complete": complete_count,
            "selected_incomplete": incomplete_count,
            "excluded_coverage_edge": excluded["coverage_edge"],
            "excluded_incomplete": excluded["incomplete"],
        },
        "instances": output_instances,
        "interpretation_boundary": {
            "descriptive_only": True,
            "research_session_convention": True,
            "not_ict_kill_zone": True,
            "not_poc": True,
            "not_value_area": True,
            "not_trading_signal": True,
            "missing_data_does_not_shift_session_boundaries": True,
        },
    }
