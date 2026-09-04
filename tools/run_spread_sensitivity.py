from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_core.spread_sensitivity import run_spread_sensitivity


def main() -> int:
    parser = argparse.ArgumentParser(description="Run frozen fixed-spread sensitivity on a gross signal result JSON.")
    parser.add_argument("gross_result_json")
    parser.add_argument("--output")
    parser.add_argument("--include-ledger", action="store_true")
    args = parser.parse_args()

    result = run_spread_sensitivity(
        args.gross_result_json,
        repo_root=ROOT,
        include_adjusted_ledger=args.include_ledger,
    )
    compact = {
        "trade_count": result["trade_count"],
        "primary_scenario": result["primary_gate"]["scenario_id"],
        "primary_passed": result["primary_gate"]["passed"],
        "scenarios": {
            scenario_id: {
                "spread_points": record["spread_points"],
                "expectancy_R": record["metrics"]["overall"]["expectancy"],
                "profit_factor": record["metrics"]["overall"]["profit_factor"],
                "max_drawdown_R": record["metrics"]["overall"]["max_drawdown"],
                "positive_months": record["metrics"]["positive_month_count"],
                "eligible_months": record["metrics"]["eligible_month_count"],
            }
            for scenario_id, record in result["scenario_results"].items()
        },
    }
    print(json.dumps(compact, indent=2))
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
