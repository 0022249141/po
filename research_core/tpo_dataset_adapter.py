from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from .data_validation import TIMEFRAME_SECONDS, _norm_row, extract_timestamp, read_csv_rows
from .tpo_profile import CLOSED, FORMING, TPOBar, TPOProfileEngine


@dataclass(frozen=True)
class SourceDayPolicy:
    """Neutral grouping policy for source-local timestamps with unknown timezone semantics.

    A source day is only the calendar date encoded in the source timestamp. It must not be
    interpreted as Asia/London/New York, an exchange session, or a broker business day.
    """

    policy_id: str = "source_calendar_day_v1"
    timestamp_semantics: str = "source_local_unknown_timezone"
    session_semantics: str = "technical_grouping_only"

    def session_id(self, timestamp: datetime) -> str:
        return f"source-day:{timestamp.date().isoformat()}"


def _decimal_field(row: dict[str, Any], name: str) -> Decimal:
    normalized = _norm_row(row)
    value = normalized.get(name)
    if value is None or str(value).strip() == "":
        raise ValueError(f"missing {name}")
    return Decimal(str(value).replace(",", "").strip())


def _parse_cutoff(value: datetime | str) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def build_source_day_tpo(
    csv_path: str | Path,
    *,
    timeframe: str,
    cutoff: datetime | str,
    price_increment: Decimal | float | int | str,
    policy: SourceDayPolicy | None = None,
) -> dict[str, Any]:
    """Apply the operational TPO engine to an OHLC CSV with an explicit neutral day policy.

    The adapter derives closed/forming status only from bar start + timeframe versus an explicit
    cutoff. It never infers timezone, DST, London/NY/Asia sessions, or instrument tick size.
    ``price_increment`` is therefore a research parameter unless external instrument metadata
    explicitly establishes otherwise.
    """

    tf = timeframe.upper()
    if tf not in TIMEFRAME_SECONDS:
        raise ValueError(f"unsupported timeframe: {timeframe}")
    interval = timedelta(seconds=TIMEFRAME_SECONDS[tf])
    cutoff_dt = _parse_cutoff(cutoff)
    policy = policy or SourceDayPolicy()

    rows, csv_meta = read_csv_rows(csv_path)
    engine = TPOProfileEngine(price_increment)

    rows_before_or_at_cutoff = 0
    closed_rows = 0
    forming_rows = 0
    last_seen_by_session: dict[str, datetime] = {}
    first_timestamp: datetime | None = None
    last_input_timestamp: datetime | None = None

    for raw in rows:
        ts = extract_timestamp(raw)
        if ts > cutoff_dt:
            break
        rows_before_or_at_cutoff += 1
        first_timestamp = first_timestamp or ts
        last_input_timestamp = ts

        session_id = policy.session_id(ts)
        previous = last_seen_by_session.get(session_id)
        gap_before = previous is not None and ts - previous > interval
        last_seen_by_session[session_id] = ts

        close_status = CLOSED if ts + interval <= cutoff_dt else FORMING
        if close_status == CLOSED:
            closed_rows += 1
        else:
            forming_rows += 1

        engine.update(
            TPOBar(
                timestamp=ts,
                low=_decimal_field(raw, "low"),
                high=_decimal_field(raw, "high"),
                close_status=close_status,
                session_id=session_id,
                gap_before=gap_before,
            )
        )

    snapshot = engine.snapshot()
    return {
        "adapter": "source_day_tpo_v1",
        "policy": {
            "policy_id": policy.policy_id,
            "timestamp_semantics": policy.timestamp_semantics,
            "session_semantics": policy.session_semantics,
            "timezone_inference": False,
            "dst_inference": False,
            "named_market_session_inference": False,
        },
        "input": {
            "file": str(Path(csv_path)),
            "timeframe": tf,
            "cutoff": cutoff_dt.isoformat(),
            "price_increment": str(Decimal(str(price_increment))),
            "price_increment_semantics": "explicit_research_parameter_unless_external_metadata_proves_tick_size",
            "csv": csv_meta,
            "first_timestamp": first_timestamp.isoformat() if first_timestamp else None,
            "last_timestamp_at_or_before_cutoff": last_input_timestamp.isoformat() if last_input_timestamp else None,
        },
        "counts": {
            "rows_at_or_before_cutoff": rows_before_or_at_cutoff,
            "closed_rows": closed_rows,
            "forming_rows": forming_rows,
        },
        "current_source_day_profile": snapshot,
        "interpretation_boundary": {
            "descriptive_only": True,
            "not_poc": True,
            "not_value_area": True,
            "not_trading_signal": True,
            "not_london_newyork_asia_session": True,
        },
    }
