#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from research_core.session_policy import format_validation_result, validate_session_policy_file


POLICY = Path("config/session-policies/xauusd-major-sessions.yaml")


def main() -> int:
    result = validate_session_policy_file(POLICY)
    print(json.dumps(format_validation_result(result), indent=2))
    return 0 if result.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
