# Missing Historical Assets

This file tracks **historical originals named by the canonical Resource Connector Map**. Operational generated equivalents do not change an original's recovery status.

## Knowledge / RAG originals

| Original | Status | Safe generated equivalent |
|---|---|---|
| `glossary.md` | missing | `knowledge/curated/glossary.generated.md` |
| `SKILL.md` (“6-layer + verdict”) | missing | `knowledge/curated/SKILL.generated.md` |
| `MARKET_PARAMS.md` | missing | `knowledge/curated/MARKET_PARAMS.generated.md` |

## Existing translation pipeline originals

- BTMM — original translated asset missing; public label audited as **Beat the Market Maker**
- MMXM — original translated asset missing; public ICT-family label audited as **Market Maker Model**
- ICT London Close Killzone — translated original missing
- Choch Plan — translated original missing
- 1AM CRT — translated original missing; exact expansion/time rules must come from original
- referenced translated PDF collection — inventory/files missing

## Named internal systems / skills

- `rtm-fshcd` — missing; identifier remains opaque
- `smcp-v3-architecture` — missing; Secure Model Context Protocol interpretation rejected as unsupported
- `quant-engine-9phase` — missing; generic 9-stage quant workflows are not the original spec

## Data / implementation originals

- real `general-platforms` CSV sample/spec — missing; provisional intake contract exists
- exact code/commit for `rolling(center=True)` correction — missing
- historical Strategy Specifications/backtest outputs for the named internal systems — missing

## Recovery rule

An item becomes `recovered` only through the protocol in `docs/RECOVERY_PROTOCOL.md`. Never rename generated reconstruction as the historical original.
