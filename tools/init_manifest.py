from __future__ import annotations

import argparse
from pathlib import Path

from research_core.provenance import build_dataset_manifest, write_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a provenance manifest for a market CSV.")
    parser.add_argument("path")
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--market", required=True)
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--data-type", required=True)
    parser.add_argument("--timezone", required=True, dest="timezone_name")
    parser.add_argument("--timeframe")
    parser.add_argument("--normalization-timezone")
    parser.add_argument("--analysis-cutoff")
    parser.add_argument("--forming-bar-policy")
    parser.add_argument("--output")
    args = parser.parse_args()

    manifest = build_dataset_manifest(
        args.path,
        source_id=args.source_id,
        market=args.market,
        symbol=args.symbol,
        data_type=args.data_type,
        timezone_name=args.timezone_name,
        timeframe=args.timeframe,
        normalization_timezone=args.normalization_timezone,
        analysis_cutoff=args.analysis_cutoff,
        forming_bar_policy=args.forming_bar_policy,
    )
    output = Path(args.output) if args.output else Path(args.path).with_suffix(Path(args.path).suffix + ".manifest.json")
    write_manifest(manifest, output)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
