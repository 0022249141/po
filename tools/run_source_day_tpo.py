from __future__ import annotations

import argparse
import json
from pathlib import Path

from research_core.tpo_dataset_adapter import build_source_day_tpo


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the operational TPO profile using a neutral source-calendar-day grouping."
    )
    parser.add_argument("csv", help="OHLC CSV path")
    parser.add_argument("--timeframe", required=True, help="Bar timeframe, e.g. M5")
    parser.add_argument("--cutoff", required=True, help="Explicit source-timestamp cutoff, ISO format")
    parser.add_argument("--price-increment", required=True, help="Explicit research/profile price increment")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    result = build_source_day_tpo(
        args.csv,
        timeframe=args.timeframe,
        cutoff=args.cutoff,
        price_increment=args.price_increment,
    )
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
