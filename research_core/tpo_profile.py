from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any


CLOSED = "closed"
FORMING = "forming"


def _decimal(value: Any) -> Decimal:
    return Decimal(str(value))


def _to_tick(price: Any, increment: Decimal) -> int:
    return int((_decimal(price) / increment).to_integral_value(rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class TPOBar:
    timestamp: datetime
    low: Decimal | float | int | str
    high: Decimal | float | int | str
    close_status: str
    session_id: str
    gap_before: bool = False


@dataclass
class TPOProfileState:
    session_id: str | None = None
    bins: dict[int, int] = field(default_factory=dict)
    observed_session_low_tick: int | None = None
    observed_session_high_tick: int | None = None
    bars_seen: int = 0
    incomplete: bool = False
    incomplete_reasons: list[str] = field(default_factory=list)
    last_closed_timestamp: datetime | None = None


class TPOProfileEngine:
    """Deterministic current-session time-at-price occupancy profile.

    This engine implements the project operational interpretation recorded in
    ``quant/operational/AMT_TPO_PROFILE_CORE.yaml``. It does not calculate POC,
    Value Area, initiative/responsive activity, or trading signals.
    """

    def __init__(self, price_increment: Decimal | float | int | str):
        increment = _decimal(price_increment)
        if increment <= 0:
            raise ValueError("price_increment must be positive")
        self.price_increment = increment
        self.state = TPOProfileState()
        self._last_global_closed_timestamp: datetime | None = None

    def _reset_session(self, session_id: str) -> None:
        self.state = TPOProfileState(session_id=session_id)

    def mark_incomplete(self, reason: str) -> None:
        reason = str(reason).strip()
        if not reason:
            raise ValueError("incomplete reason must be non-empty")
        self.state.incomplete = True
        if reason not in self.state.incomplete_reasons:
            self.state.incomplete_reasons.append(reason)

    def update(self, bar: TPOBar) -> bool:
        status = str(bar.close_status).strip().lower()
        if status not in {CLOSED, FORMING}:
            raise ValueError("close_status must be 'closed' or 'forming'")

        session_id = str(bar.session_id).strip()
        if not session_id:
            raise ValueError("session_id must be non-empty")

        low_tick = _to_tick(bar.low, self.price_increment)
        high_tick = _to_tick(bar.high, self.price_increment)
        if high_tick < low_tick:
            raise ValueError("high must be greater than or equal to low after tick normalization")

        # Forming bars are a strict no-op and may later arrive again as closed.
        if status == FORMING:
            return False

        if self._last_global_closed_timestamp is not None and bar.timestamp <= self._last_global_closed_timestamp:
            raise ValueError("closed-bar timestamps must be strictly increasing")

        if self.state.session_id != session_id:
            self._reset_session(session_id)

        if bar.gap_before:
            self.mark_incomplete("source_gap_before_bar")

        for tick in range(low_tick, high_tick + 1):
            self.state.bins[tick] = self.state.bins.get(tick, 0) + 1

        if self.state.observed_session_low_tick is None:
            self.state.observed_session_low_tick = low_tick
            self.state.observed_session_high_tick = high_tick
        else:
            self.state.observed_session_low_tick = min(self.state.observed_session_low_tick, low_tick)
            self.state.observed_session_high_tick = max(self.state.observed_session_high_tick, high_tick)

        self.state.bars_seen += 1
        self.state.last_closed_timestamp = bar.timestamp
        self._last_global_closed_timestamp = bar.timestamp
        return True

    def tick_to_price(self, tick: int) -> Decimal:
        return self.price_increment * Decimal(tick)

    def snapshot(self) -> dict[str, Any]:
        return {
            "session_id": self.state.session_id,
            "price_increment": str(self.price_increment),
            "bins": dict(sorted(self.state.bins.items())),
            "observed_session_low_tick": self.state.observed_session_low_tick,
            "observed_session_high_tick": self.state.observed_session_high_tick,
            "bars_seen": self.state.bars_seen,
            "incomplete": self.state.incomplete,
            "incomplete_reasons": list(self.state.incomplete_reasons),
            "last_closed_timestamp": (
                self.state.last_closed_timestamp.isoformat()
                if self.state.last_closed_timestamp is not None
                else None
            ),
        }
