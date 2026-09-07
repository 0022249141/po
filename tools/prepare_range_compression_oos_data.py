from __future__ import annotations
import argparse
import json
from pathlib import Path
from research_core.range_compression_oos_data import prepare_oos_data

parser = argparse.ArgumentParser(description="Prepare canonical MT5 UTC data for prospective OOS state initialization.")
parser.add_argument("manifest")
parser.add_argument("--output", required=True)
args = parser.parse_args()
output = Path(args.output).expanduser()
if output.exists():
    raise SystemExit(f"refusing to overwrite existing output: {output}")
result = prepare_oos_data(args.manifest)
output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["status"] == "ready" else 1)
