import json
from pathlib import Path
from research_core.range_compression_oos_validation import validate_range_compression_oos_spec
root=Path(__file__).resolve().parents[1]
result=validate_range_compression_oos_spec(repo_root=root)
print(json.dumps({'status':result.status,'errors':result.errors,'warnings':result.warnings}, indent=2))
raise SystemExit(0 if result.status == 'pass' else 1)
