from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_core.regime_result_summary import summarize_regime_result_file


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print a compact audit summary from a raw regime robustness JSON result."
    )
    parser.add_argument("json_result", help="Path to named_session_tpo_regime_robustness_v1.json")
    args = parser.parse_args()

    summary = summarize_regime_result_file(args.json_result)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
