# Cross-Framework Boundaries

## Purpose

Permit comparison without collapsing distinct trading schools into one vocabulary.

| Question | ICT/SMC | RTM | Wyckoff | Auction Market Theory | Academic Microstructure |
|---|---|---|---|---|---|
| Primary object | price delivery / liquidity / PD arrays (source-specific) | price-action structures and RTM-specific zones | campaign/phase/effort-result concepts | auction/value/profile behavior | formal models of information, inventory, liquidity |
| Typical data | OHLC/time/session; sometimes derived concepts | OHLC/price-action | price + volume where methodology uses it | profile/volume/TPO depending implementation | model/data dependent |
| Can infer live dealer inventory? | No | No | No | No | Theory models inventory; live inference requires actual data |
| Default backtest status | subjective until operationalized | subjective until operationalized | many concepts subjective until formalized | implementation-dependent | equations may be formal; mapping to trade rules is separate |

## Non-equivalence rules

- RTM FTR is not automatically an ICT Order Block.
- Wyckoff Spring/Upthrust is not automatically a Liquidity Sweep under a fixed ICT rule.
- AMT responsive/initiative activity is not automatically BOS/MSS.
- Academic inventory-risk theory is not evidence that a particular bank/dealer is currently long or short.
- Similar chart shapes do not establish conceptual equivalence.

## Crosswalk status tags

- `same_definition` — only with explicit source evidence
- `rough_analogy` — similar use, different definition
- `implementation_overlap` — can map to same coded feature under a specified rule
- `not_equivalent`
- `unknown`
