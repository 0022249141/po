from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_core.regime_robustness import run_named_session_tpo_regime_robustness


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the frozen named-session TPO causal lagged-range regime robustness study."
    )
    parser.add_argument("csv", help="Canonical timezone-aware UTC OHLC CSV")
    parser.add_argument(
        "--spec",
        default="quant/studies/XAUUSD_NAMED_SESSION_TPO_REGIME_ROBUSTNESS_V1.yaml",
        help="Regime robustness study specification relative to repository root",
    )
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    result = run_named_session_tpo_regime_robustness(
        args.csv,
        spec_path=args.spec,
        repo_root=ROOT,
    )
    text = json.dumps(result, indent=2)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote: {output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
