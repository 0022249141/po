from __future__ import annotations

import argparse
import json

from research_core.mtf_qualification import qualify_bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Qualify an H1/M15/M5/Tick XAUUSD export bundle.")
    parser.add_argument("--h1", required=True)
    parser.add_argument("--m15", required=True)
    parser.add_argument("--m5", required=True)
    parser.add_argument("--tick", required=True)
    args = parser.parse_args()

    result = qualify_bundle(h1_path=args.h1, m15_path=args.m15, m5_path=args.m5, tick_path=args.tick)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    mismatch_count = 0
    for value in result["cross_timeframe"].values():
        mismatch_count += value["ohlc_mismatches"]
    for value in result["tick_reconstruction"].values():
        mismatch_count += value["ohlc_mismatches"]
    return 1 if mismatch_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
