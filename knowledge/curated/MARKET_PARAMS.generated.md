# Market Parameters — Generated Operational Contract

> Not the recovered historical `MARKET_PARAMS.md`. Numeric values remain unset unless provided by an actual data source/broker/specification.

## Required per-market parameters

### Identity
- canonical market id
- symbol and source-specific aliases
- asset class
- price currency/unit

### Time
- source timezone
- normalization timezone
- session/calendar definition
- daylight-saving rule where relevant
- candle timestamp convention (open-time vs close-time)

### Price / contract
- tick size
- price precision
- contract size where applicable
- minimum/step volume when execution research needs it

### Data
- primary source id
- allowed secondary/cross-check source ids
- data type and timeframe
- forming-bar policy
- missing-row policy
- duplicate policy

### Execution research
- spread model
- commission model
- slippage model
- order timing
- fill priority / intrabar assumptions

## Current project profiles

### XAUUSD
Canonical map roles:
- broker/user export: primary user-provided analysis feed when supplied
- Dukascopy: historical parallel dataset for backtesting
- TradingView: visual cross-check / community implementation review
- TradingEconomics + ForexFactory: macro-event context

No broker-specific digits, contract size, tick size or session assumptions are hard-coded here.

### Iran melted gold
Canonical map roles:
- `general_platforms_csv`: primary intraday feed according to the map, exact schema pending real sample
- TGJU: independent price cross-check, not assumed to expose a stable public API

Exact OTC session/price-unit rules must come from the project’s canonical user data/config before automated analysis.
