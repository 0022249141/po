import argparse, json
from pathlib import Path
from research_core.range_compression_oos import account_oos

p=argparse.ArgumentParser(); p.add_argument('--trades', required=True); p.add_argument('--reference', required=True); p.add_argument('--output'); a=p.parse_args()
result=account_oos(json.loads(Path(a.trades).read_text()), json.loads(Path(a.reference).read_text()))
text=json.dumps(result, indent=2)+'\n'
if a.output: Path(a.output).write_text(text, encoding='utf-8')
else: print(text)
