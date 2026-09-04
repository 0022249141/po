from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from research_core.metrics import summarize_trades


def _normalize(row: dict[str, str]) -> dict[str, str]:
    n = {str(k).strip().lower().replace(" ", "_"): v for k, v in row.items() if k is not None}
    pnl = n.get("pnl", n.get("profit", n.get("net_profit")))
    if pnl is None:
        raise ValueError("CSV requires a pnl/profit/net_profit column")
    return {"pnl": pnl, "side": n.get("side", n.get("direction", "unknown"))}


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize trade-level backtest P&L without claiming strategy validity.")
    parser.add_argument("path")
    parser.add_argument("--initial-capital", type=float, default=0.0)
    args = parser.parse_args()

    with Path(args.path).open("r", encoding="utf-8-sig", newline="") as fh:
        rows = [_normalize(r) for r in csv.DictReader(fh)]
    report = summarize_trades(rows, initial_capital=args.initial_capital)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
