# Quant / Backtesting Protocol

## Required sequence

1. Research question
2. Operational definition
3. Strategy Specification freeze
4. Data manifest + cutoff
5. Baseline implementation
6. Execution/cost model
7. Lookahead/repainting audit
8. In-Sample run
9. Out-of-Sample run
10. Robustness checks
11. Result registry
12. Claim classification

## Specification freeze

Before code, define:

- market/symbol/timeframe/session
- swing/pivot rule
- structure event rule (if used)
- entry sequence and exact trigger
- stop/invalidation
- exit/target
- cancellation/no-trade conditions
- sizing
- commission/spread/slippage
- order timing and fill assumptions
- any warm-up / confirmation delay

A code convenience is not permission to mutate a rule.

## Mandatory audit questions

- Does any calculation use future bars (`shift(-n)`, centered rolling, future-index reference)?
- Are pivot labels delayed until confirmation or painted retrospectively as if known earlier?
- Does Pine use `barmerge.lookahead_on` or equivalent future leakage?
- Are entries filled at prices unavailable at decision time?
- Are stops/targets evaluated with unrealistic intrabar priority?
- Are transaction costs omitted?
- Was the same sample used for design, parameter selection and final evaluation?

## Required result fields

At minimum:

- trade count
- net profit
- profit factor
- expectancy
- maximum drawdown
- average win / loss
- average trade
- win rate (context only, never alone)
- consecutive losses
- long vs short performance
- cost assumptions
- IS/OOS split
- robustness notes

## Claim states

- `idea` — conceptual only
- `specified` — operational rules frozen
- `implemented` — code exists and passes basic tests
- `backtested` — reproducible run exists
- `oos_checked` — OOS evidence exists
- `robustness_checked` — perturbation/regime checks exist
- `validated_for_scope` — evidence supports the stated limited scope only
- `rejected` — evidence contradicts acceptance criteria

No result is “high probability”, “institutional” or “validated” because an AI model says so.
