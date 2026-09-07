from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_core.range_compression_study import run_range_compression_study


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the frozen XAUUSD pre-New-York range-compression post-hoc diagnostic."
    )
    parser.add_argument(
        "--spec",
        default="quant/studies/XAUUSD_NY_PREOPEN_RANGE_COMPRESSION_EXPLORATORY_V1.yaml",
        help="Frozen study specification relative to the repository root",
    )
    parser.add_argument("--output", help="Optional new JSON artifact path; existing files are never overwritten")
    args = parser.parse_args()

    result = run_range_compression_study(spec_path=args.spec, repo_root=ROOT)
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        output = Path(args.output)
        if not output.is_absolute():
            output = ROOT / output
        if output.exists():
            raise FileExistsError(f"refusing to overwrite existing output: {output}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"Wrote: {output}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
