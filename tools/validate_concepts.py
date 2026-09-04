from __future__ import annotations

import json
import sys

from research_core.concept_validation import format_result, validate_concept_registry


def main() -> int:
    result = validate_concept_registry(".")
    print(json.dumps(format_result(result), indent=2))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
