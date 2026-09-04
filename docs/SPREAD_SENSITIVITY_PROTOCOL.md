# Spread Sensitivity Protocol

## Scope

This stage follows a gross signal-research result that passed its pre-frozen gate. It does **not**
change signal rules and it is **not** a full broker execution backtest.

## Why this stage exists

The canonical M5 backtest is gross and zero-cost. The canonical tick snapshot contains bid/ask
quotes only from 2026-09-02 through 2026-09-04, while the strategy sample spans March through
September. Therefore the project cannot honestly claim a full-sample historical spread model.

The first cost follow-up is consequently a fixed-spread **sensitivity test**, using the exact
min/median/max spread-point statistics already recorded in the canonical manifest:

- 12 points: observed minimum sensitivity
- 22 points: observed median and pre-frozen primary gate
- 151 points: observed maximum stress-only scenario

Point size is 0.01.

## Adjustment rule

For each trade:

`spread_price = spread_points * point_size`

`spread_cost_R = spread_price / initial_risk`

`adjusted_R = gross_R - spread_cost_R`

This is one full-spread round-trip deduction. It is intentionally side-symmetric in R accounting.
It does not recompute trigger timing, ask-side stop touches, or gap paths.

## Primary gate

The 22-point observed-median fixed-spread scenario must retain:

- expectancy R > 0
- profit factor > 1

If it fails, signal rules are not tuned. A new strategy version would be required for any rule
change.

## Boundaries

Passing this stage still does not establish net profitability. Commission and slippage remain
unresolved, and the historical bid/ask execution path is not reconstructed for the full sample.
No live-trading permission follows from this stage.
