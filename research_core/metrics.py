from __future__ import annotations

from typing import Iterable, Mapping, Any


def _profit_factor(pnls: list[float]) -> float | None:
    gross_profit = sum(x for x in pnls if x > 0)
    gross_loss = -sum(x for x in pnls if x < 0)
    if gross_loss == 0:
        return None
    return gross_profit / gross_loss


def _max_consecutive_losses(pnls: list[float]) -> int:
    best = current = 0
    for pnl in pnls:
        if pnl < 0:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def _drawdown(pnls: list[float], initial_capital: float) -> tuple[float, float | None]:
    equity = float(initial_capital)
    peak = equity
    max_dd = 0.0
    max_dd_pct: float | None = 0.0 if equity > 0 else None
    for pnl in pnls:
        equity += pnl
        if equity > peak:
            peak = equity
        dd = peak - equity
        max_dd = max(max_dd, dd)
        if peak > 0:
            pct = dd / peak
            if max_dd_pct is None or pct > max_dd_pct:
                max_dd_pct = pct
    return max_dd, max_dd_pct


def summarize_pnls(pnls: Iterable[float], initial_capital: float = 0.0) -> dict[str, Any]:
    values = [float(x) for x in pnls]
    wins = [x for x in values if x > 0]
    losses = [x for x in values if x < 0]
    max_dd, max_dd_pct = _drawdown(values, initial_capital)
    count = len(values)
    gross_profit = sum(wins)
    gross_loss_signed = sum(losses)
    return {
        "trades": count,
        "net_profit": sum(values),
        "gross_profit": gross_profit,
        "gross_loss": gross_loss_signed,
        "profit_factor": _profit_factor(values),
        "profit_factor_note": "undefined_no_losses" if values and not losses else None,
        "expectancy": (sum(values) / count) if count else None,
        "average_trade": (sum(values) / count) if count else None,
        "average_win": (sum(wins) / len(wins)) if wins else None,
        "average_loss": (sum(losses) / len(losses)) if losses else None,
        "win_rate": (len(wins) / count) if count else None,
        "wins": len(wins),
        "losses": len(losses),
        "breakeven": count - len(wins) - len(losses),
        "max_consecutive_losses": _max_consecutive_losses(values),
        "max_drawdown": max_dd,
        "max_drawdown_pct": max_dd_pct,
        "initial_capital": initial_capital,
    }


def normalize_side(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"long", "buy", "b", "1"}:
        return "long"
    if text in {"short", "sell", "s", "-1"}:
        return "short"
    return "unknown"


def summarize_trades(trades: Iterable[Mapping[str, Any]], initial_capital: float = 0.0) -> dict[str, Any]:
    rows = list(trades)
    pnls = [float(r["pnl"]) for r in rows]
    result = summarize_pnls(pnls, initial_capital=initial_capital)
    by_side: dict[str, dict[str, Any]] = {}
    for side in ("long", "short", "unknown"):
        subset = [float(r["pnl"]) for r in rows if normalize_side(r.get("side")) == side]
        if subset:
            by_side[side] = summarize_pnls(subset, initial_capital=0.0)
    result["by_side"] = by_side
    return result
