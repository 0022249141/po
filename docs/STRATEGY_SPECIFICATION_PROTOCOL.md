# Strategy Specification Protocol

## Purpose

This protocol governs the first transition from descriptive market research into a falsifiable trading-rule candidate.
A frozen strategy signal specification is not evidence of edge and is not permission to trade.

## V1 baseline

The first project baseline is `xauusd_ny_preopen_range_breakout_baseline_v1`.
It is intentionally simple and framework-neutral. It must not be relabeled as ICT, SMC, RTM, AMT, dealer logic, or a final project strategy.

## Causal reference window

For each eligible New York research-session date, build a four-hour M5 reference window immediately preceding the policy-defined New York open.
The window must contain exactly 48 present, closed M5 bars, and every reference bar must also classify as London under the named-session policy.
The reference high is the maximum high; the reference low is the minimum low.
Any missing bar, coverage problem, forming bar, or non-London reference membership produces `NO TRADE` for that date.

## Signal rule

During the first four hours of the New York research session, the first closed M5 bar that closes strictly above the frozen reference high is a long trigger; the first closed M5 bar that closes strictly below the reference low is a short trigger.
Only the first qualifying trigger is admitted. Entry is at the next M5 bar open, never at the trigger-bar close. At most one trade is allowed per session.

## Stop and exit

The structural stop remains the opposite side of the pre-New-York reference range: reference low for long and reference high for short. It may not be widened.
V1 deliberately has no profit target, partial exit, or trailing stop. The non-stop exit is the New York research-session end.

## Regime handling

The existing causal low/normal/high regime may be attached to a trade for reporting and stratification only. It may not suppress an entry, choose direction, alter stop placement, or otherwise change V1 behavior.

## Execution boundary

The signal rules are frozen before the historical execution-cost model is qualified. Broker bar price-side semantics, spread-fill semantics, commission, slippage, same-bar stop behavior, and gap behavior remain explicit execution blockers for any net-profitability or live-trading claim.
A signal-level backtest may be built next, but no result may be described as executable net edge until a separate bound execution model is frozen and validated.

## Pre-test acceptance gate

V1 is a falsification baseline. Before results are observed, the project freezes minimum sample and gross R-metric gates in the strategy YAML. If V1 fails, the frozen version is rejected rather than tuned in place. Any signal-rule modification creates a new version.

## No framework substitution

The descriptive finding that New York exhibited larger historical session range and occupancy activity does not prove a breakout strategy. This baseline tests a new hypothesis. No SMC/ICT/RTM concept may be inserted into V1 after results are observed without creating a separately specified strategy version.
