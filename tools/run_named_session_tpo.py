#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from research_core.named_session_dataset import (
    ALLOW_INCOMPLETE_WITH_FLAG,
    COMPLETE_ONLY,
    SessionSelectionPolicy,
    build_named_session_tpo,
)
from research_core.session_policy import NamedSessionPolicy


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build descriptive TPO occupancy profiles for explicit IANA/DST-aware named sessions."
    )
    parser.add_argument("csv", help="Canonical timezone-aware OHLC CSV")
    parser.add_argument("--timeframe", default="M5")
    parser.add_argument("--cutoff", required=True, help="Timezone-aware cutoff, preferably UTC/Z")
    parser.add_argument("--price-increment", required=True)
    parser.add_argument(
        "--session-policy",
        default="config/session-policies/xauusd-major-sessions.yaml",
    )
    parser.add_argument(
        "--sessions",
        nargs="+",
        default=["asia_tokyo", "london", "new_york"],
    )
    parser.add_argument(
        "--completeness",
        choices=[COMPLETE_ONLY, ALLOW_INCOMPLETE_WITH_FLAG],
        default=COMPLETE_ONLY,
    )
    parser.add_argument(
        "--include-coverage-edges",
        action="store_true",
        help="Diagnostic only; project backtest default excludes coverage-edge sessions.",
    )
    parser.add_argument("--output", default="named_session_tpo.json")
    args = parser.parse_args()

    policy = NamedSessionPolicy.from_yaml(args.session_policy)
    result = build_named_session_tpo(
        args.csv,
        timeframe=args.timeframe,
        cutoff=args.cutoff,
        price_increment=args.price_increment,
        session_policy=policy,
        session_ids=args.sessions,
        selection_policy=SessionSelectionPolicy(
            completeness_mode=args.completeness,
            exclude_coverage_edges=not args.include_coverage_edges,
        ),
    )

    output = Path(args.output).expanduser().resolve()
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "pass",
                "adapter": result["adapter"],
                "session_policy_id": result["session_policy_id"],
                "selection_policy": result["selection_policy"],
                "counts": result["counts"],
                "output": str(output),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
