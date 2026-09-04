# Signal Backtest Protocol

Status: operational research protocol for the first frozen XAUUSD strategy baseline.

## Scope

This stage evaluates the already-frozen signal specification
`xauusd_ny_preopen_range_breakout_baseline_v1` on canonical closed M5 bars. It is deliberately a
**gross signal study**, not a broker-accurate net backtest and not a live-trading approval.

## Frozen evaluation semantics

- Input must be verified UTC M5 data.
- The New York session must be complete through its research-policy end before it is evaluated.
- The four-hour pre-New-York reference range must contain exactly 48 present, closed M5 bars and
  every one of those bars must classify as London under the named-session policy.
- Trigger uses the first qualifying **closed** M5 bar during the first four hours of New York.
- Entry fill is the next M5 bar open; same-trigger-bar fills are prohibited.
- Structural stop is the opposite reference-range boundary.
- Stop is active on the entry bar.
- If a bar opens through the stop, gross research fill is the bar open; otherwise a stop touch fills
  at the stop level. This permits outcomes below -1R after gaps.
- With no stop hit, the trade exits at the final closed M5 bar close of the New York session.
- Commission, spread and slippage are zero in this stage. Therefore results are **gross only**.

## Reporting

The run must write a deterministic trade ledger plus:

- gross expectancy in R,
- gross profit factor,
- max drawdown in R,
- long/short splits,
- calendar-month splits,
- Low/Normal/High regime splits as reporting dimensions only.

Regime labels may not filter entries or change direction in V1.

## Pre-test acceptance gate

The frozen strategy specification controls acceptance. V1 requires at minimum 60 total trades,
20 long trades, 20 short trades, positive gross expectancy, gross PF above 1.0, and at least four
positive eligible calendar months. An eligible month is frozen here as any month with at least one
evaluated trade.

Failure means **reject V1 without parameter tuning**. A different reference window, trigger rule,
stop, target or filter requires a new strategy version rather than a silent edit.

## Interpretation boundary

Passing this stage would establish only a candidate gross signal edge on this canonical sample.
Before any promotion, the project still requires broker-side price semantics, spread, commission,
slippage, execution-cost sensitivity, out-of-sample validation and robustness checks. Passing is
not permission to trade live.
