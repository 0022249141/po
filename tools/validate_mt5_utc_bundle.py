#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from research_core.mt5_utc_bundle import validate_utc_bundle_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a canonical MT5 UTC bundle binding manifest and file hashes.")
    parser.add_argument("manifest", help="Path to binding_manifest.json")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    result = validate_utc_bundle_manifest(payload, manifest_path.parent)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] != "fail" else 1


if __name__ == "__main__":
    raise SystemExit(main())
