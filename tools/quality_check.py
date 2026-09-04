from __future__ import annotations

import json

from research_core.lookahead import scan_path
from research_core.registry import validate_source_registry


def main() -> int:
    registry = validate_source_registry("config/source-registry.yaml")
    lookahead = scan_path(".")
    high = [f for f in lookahead if f["severity"] == "high"]
    result = {
        "registry": registry,
        "lookahead_findings": lookahead,
        "status": "fail" if registry["status"] == "fail" or high else "pass",
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
