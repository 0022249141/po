# Integration Matrix

This repository contains **integration policy**, not an MCP runtime.

| System/source | Role | Storage/retrieval approach | Write/execution authority |
|---|---|---|---|
| GitHub | canonical project/versioning | repo connector / git clone | repository files only |
| ChatGPT | research/retrieval/analysis | consume curated files + source registry | no trading execution |
| Google Drive (optional) | large translated PDFs/source archive | external source library | source-file management depends connector permissions |
| MT5 exports | user/broker market data | CSV/tick files + manifests | import/read for research; no order execution in this repo |
| Dukascopy | historical XAUUSD parallel data | external download + manifest | read/research |
| TradingView | visual cross-check and strategy implementation | chart/manual export/Pine source | no assumed API connector |
| TGJU | Iran-gold cross-check | web/extraction if permitted | read-only reference |
| TradingEconomics / ForexFactory | macro event context | external retrieval + normalized event table | read-only research |

## Retrieval priority for ChatGPT

1. user-supplied current dataset/file
2. frozen Strategy Specification / validated run record
3. curated project artifacts
4. source-specific notes
5. canonical source registry/map
6. external web/source lookup when requested/required

Never let hidden memory override a newer supplied dataset or specification.
