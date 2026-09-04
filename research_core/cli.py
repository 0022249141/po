from __future__ import annotations

import argparse
import json
from pathlib import Path

from .data_validation import validate_market_csv
from .lookahead import scan_path


def validate_csv_main() -> int:
    parser = argparse.ArgumentParser(description="Validate OHLC/tick CSV data for research use.")
    parser.add_argument("path")
    parser.add_argument("--type", choices=["ohlc", "tick"], required=True, dest="data_type")
    parser.add_argument("--timeframe", default=None)
    args = parser.parse_args()
    report = validate_market_csv(args.path, args.data_type, timeframe=args.timeframe)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["status"] == "fail" else 0


def audit_lookahead_main() -> int:
    parser = argparse.ArgumentParser(description="Static scan for common lookahead/future-leakage patterns.")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--fail-on", choices=["none", "high", "review"], default="none")
    args = parser.parse_args()
    findings = scan_path(args.path)
    result = {"findings": findings, "count": len(findings)}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if args.fail_on == "high" and any(f["severity"] == "high" for f in findings):
        return 2
    if args.fail_on == "review" and findings:
        return 2
    return 0
