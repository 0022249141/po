from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research_core.strategy_spec_validation import (
    format_result,
    validate_repository_strategy_specs,
)


def main() -> int:
    result = validate_repository_strategy_specs(ROOT)
    print(json.dumps(format_result(result), indent=2))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
