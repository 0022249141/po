from __future__ import annotations

import argparse
import json
from pathlib import Path

from research_core.signal_evaluation_validation import format_validation_result, validate_signal_evaluation_file


DEFAULT = "quant/candidates/XAUUSD_NY_PREOPEN_RANGE_BREAKOUT_BASELINE_V1.evaluation.yaml"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate frozen gross signal-evaluation semantics.")
    parser.add_argument("path", nargs="?", default=DEFAULT)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    result = validate_signal_evaluation_file(Path(args.path), Path(args.repo_root))
    print(json.dumps(format_validation_result(result), indent=2))
    return 0 if not result.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
