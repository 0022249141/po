from __future__ import annotations

import argparse
import json
from pathlib import Path

from research_core.strategy_signal_backtest import run_strategy_signal_backtest


def main() -> int:
    parser = argparse.ArgumentParser(description="Run frozen XAUUSD gross signal backtest baseline.")
    parser.add_argument("csv")
    parser.add_argument("--output", required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--no-regime-report", action="store_true")
    args = parser.parse_args()

    result = run_strategy_signal_backtest(
        args.csv,
        repo_root=args.repo_root,
        include_regime_reporting=not args.no_regime_report,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")

    overall = result["metrics"]["overall"]
    acceptance = result["acceptance"]
    compact = {
        "trade_count": result["trade_count"],
        "expectancy_R": overall.get("expectancy"),
        "profit_factor": overall.get("profit_factor"),
        "max_drawdown_R": overall.get("max_drawdown"),
        "long_trades": result["metrics"]["by_side"]["long"]["trades"],
        "short_trades": result["metrics"]["by_side"]["short"]["trades"],
        "positive_months": result["metrics"]["positive_month_count"],
        "eligible_months": result["metrics"]["eligible_month_count"],
        "acceptance_passed": acceptance["passed"],
        "acceptance_checks": acceptance["checks"],
    }
    print(json.dumps(compact, indent=2))
    print(f"Wrote: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
