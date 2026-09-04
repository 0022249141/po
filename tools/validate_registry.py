from __future__ import annotations

import argparse
import json

from research_core.registry import validate_source_registry


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate config/source-registry.yaml.")
    parser.add_argument("path", nargs="?", default="config/source-registry.yaml")
    args = parser.parse_args()
    report = validate_source_registry(args.path)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
