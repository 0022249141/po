# Data Protocol

## Purpose

Prevent market analysis and backtesting from silently using malformed, stale, future, or provenance-free data.

## Required dataset metadata

Every dataset must have a manifest containing at minimum:

- stable dataset id
- market and symbol
- source id
- data type (`ohlc`, `tick`, `macro_event`, etc.)
- timeframe when applicable
- source timezone and normalization timezone
- earliest/latest timestamp
- analysis cutoff when used in a study
- whether forming candles are present/allowed
- row count
- SHA-256 checksum
- validation status and validator version

## Intake gates

### Gate D1 — identity
Symbol/market must be explicit. Alias mapping must be documented rather than guessed.

### Gate D2 — timestamps
Timezone must be known. Naive timestamps may be stored only when source-local timezone is separately explicit.

### Gate D3 — ordering and duplicates
Rows must be ordered for time-series use. Duplicate timestamps are reported. Duplicate handling must be specified, not silently dropped.

### Gate D4 — price integrity
OHLC rows must satisfy `high >= max(open, close, low)` and `low <= min(open, close, high)`. Tick rows must not have `bid > ask` unless the source semantics explicitly justify it.

### Gate D5 — gaps
Expected-interval gaps are reported. Market closures are not automatically classified as missing-data defects; the report is evidence for later session-aware review.

### Gate D6 — closed vs forming
Any analysis that confirms BOS/MSS/pivots on closed candles must state and enforce the candle cutoff. Forming bars cannot be silently promoted to confirmed structure.

### Gate D7 — source hierarchy
For XAUUSD, user/broker exports, Dukascopy historical data and TradingView visual cross-checks have different roles. They are not assumed numerically identical. For Iran gold, the canonical map treats the existing `general-platforms` feed as the intraday source and TGJU as cross-check; exact implementation awaits a real sample.

## Storage policy

Large raw market files are excluded from Git by default. Store manifests, schemas, small approved samples and derived reproducible results in Git; store bulk datasets in an appropriate external location and reference them by checksum/path.
