from __future__ import annotations

import json
from pathlib import Path

from research_core.framework_validation import format_result, validate_framework_ingestion


def main() -> int:
    result = validate_framework_ingestion(Path.cwd())
    print(json.dumps(format_result(result), indent=2, ensure_ascii=False))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
