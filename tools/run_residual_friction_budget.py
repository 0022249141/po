from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_core.residual_friction_budget import run_residual_friction_budget


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute residual round-trip price-friction budget after the frozen median-spread case.")
    parser.add_argument("gross_result_json")
    parser.add_argument("--spec", default="quant/candidates/XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.residual_friction_budget.yaml")
    parser.add_argument("--output")
    args = parser.parse_args()

    result = run_residual_friction_budget(args.gross_result_json, spec_path=args.spec, repo_root=ROOT)
    budget = result["residual_friction_budget"]
    base = result["base_primary_spread"]
    compact = {
        "trade_count": result["trade_count"],
        "base_spread_points": base["spread_points"],
        "base_expectancy_R": base["metrics"]["expectancy"],
        "base_profit_factor": base["metrics"]["profit_factor"],
        "break_even_extra_round_trip_price": budget["break_even_extra_round_trip_price"],
        "break_even_extra_round_trip_points": budget["break_even_extra_round_trip_points"],
        "total_break_even_round_trip_points": budget["total_break_even_round_trip_points_including_primary_spread"],
    }
    print(json.dumps(compact, indent=2))

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Wrote: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
