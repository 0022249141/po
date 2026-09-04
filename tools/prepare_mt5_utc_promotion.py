#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from research_core.canonical_dataset import build_promotion_record


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a canonical MT5 UTC bundle and emit a compact promotion record."
    )
    parser.add_argument("manifest", help="Path to the freshly generated binding_manifest.json")
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output path. Default: <bundle-folder>/promotion_record.json",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    try:
        record = build_promotion_record(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "fail", "errors": [str(exc)], "warnings": []}, indent=2))
        return 1

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else manifest_path.parent / "promotion_record.json"
    )
    output_path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps({
        "status": "pass",
        "dataset_id": record["dataset_id"],
        "symbol": record["symbol"],
        "broker_feed_identity": record["timebase"]["broker_feed_identity"],
        "timebase_status": record["status"],
        "source_timezone": record["timebase"]["source_timezone"],
        "named_session_use_allowed": record["timebase"]["named_session_use_allowed"],
        "session_policy_id": record["session_policy_authorization"]["policy_id"],
        "binding_manifest_sha256": record["provenance"]["binding_manifest_sha256"],
        "file_count": len(record["files"]),
        "promotion_record": str(output_path),
        "errors": [],
        "warnings": [],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
