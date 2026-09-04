# XAUUSD Data

## Sources named by the canonical map

- **Dukascopy** — historical tick/minute data for parallel backtesting.
- **MT5 exports** — user-provided operational market data when supplied.
- **TradingView** — visual cross-check and community-script implementation review.
- **TradingEconomics / ForexFactory** — macro-event metadata for Time Logic / Volatility State.

## Data roles

These sources are not interchangeable. Every analysis/backtest must state which provider generated the data and must not splice providers without an explicit normalization step.

## Validation checklist

- symbol/provider identity
- timezone and DST treatment
- digits/tick size
- bid/ask/mid construction
- spread availability
- timestamp cutoff
- closed vs forming bars
- gaps and duplicates
- session boundaries
- resampling method
- transaction-cost assumptions

## Backtest use

Dukascopy is intended as an independent historical benchmark against broker/MT5 data. Differences between feeds must be measured rather than assumed negligible.

## TradingView role

TradingView is a chart/visual and implementation cross-check layer in this architecture. A community script does not constitute validation of a trading concept.
