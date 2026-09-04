# ICT / SMC / Wyckoff Operationalization Rules

## Principle

A visual concept becomes testable only after every decision boundary is explicit.

## Required fields for structure concepts

For any Swing/BOS/CHoCH/MSS implementation specify:

- swing algorithm (left/right bars, ATR threshold, fractal, zigzag, etc.)
- confirmation delay
- wick vs close break
- minimum break distance
- timeframe
- whether equal highs/lows have tolerance
- whether current/forming bars are allowed

## FVG

Specify:
- exact three-candle condition
- wick vs body reference
- minimum gap size
- whether partial fill counts as mitigation
- full-fill definition
- expiration rule
- first-return vs any-return policy

## Liquidity Sweep

Specify:
- reference level construction
- tolerance
- excursion requirement
- reclaim/close requirement if any
- maximum confirmation window

A sweep by itself does not encode reversal.

## Wyckoff

Labels such as accumulation/distribution/spring/upthrust require objective event and phase rules before coding. If such rules are unavailable, retain `DISCRETIONARY` status and do not claim statistical validation.
