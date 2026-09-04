# Operationalization Gate

## Purpose

This gate controls promotion from a source-faithful `defined` concept into `operational_candidate`, `operational`, and later `backtest_ready` states.

A concept is not promoted merely because it has a plausible chart interpretation. Promotion requires an explicit rule that can be implemented without visual hindsight and can be audited against the exact data available.

## Preconditions

A concept entering this gate must:

1. exist in `knowledge/CONCEPT_REGISTRY.yaml`;
2. be at least `defined`;
3. retain exact evidence and definition paths;
4. remain inside its native framework;
5. not depend on an unstated cross-framework substitution.

## Mandatory machine-rule fields

An operational candidate must explicitly state:

- `instrument_scope`
- `input_data`
- `timeframe_or_event_clock`
- `lookback`
- `reference_set`
- `state_variables`
- `trigger`
- `confirmation`
- `invalidation`
- `entry_timing` when the concept is used for entry
- `exit_or_target` when the concept is used for exit/targeting
- `forming_bar_policy`
- `timezone_or_session_dependency`
- `missing_data_policy`
- `tie_and_edge_case_policy`
- `measurable_proxy` when the source concept is theoretical and not directly observable

A field may be explicitly `not_applicable` only when the reason is documented.

## Promotion states

- `blocked` — definition exists but one or more machine-rule dependencies are unresolved.
- `candidate` — all mandatory fields are explicit enough for implementation review; no backtest claim exists.
- `operational` — implementation boundary is frozen and passes rule audit without hindsight/lookahead.
- `backtest_ready` — an immutable Strategy Specification links the rule to data, execution model, costs, and evaluation protocol.

These readiness states do not replace the concept-ingestion state; they are a separate operationalization audit.

## Non-signal theoretical concepts

Dealer / market-microstructure concepts such as inventory risk, adverse selection, immediacy, and informed trading are not price-chart signals by themselves. To become operational candidates they require a measurable observable proxy, the proxy's data source, sampling rule, lag policy, and a documented argument for why the proxy represents the intended theoretical variable.

No OHLC pattern may be relabelled as direct dealer inventory, bank positioning, hidden orders, DOM, CVD, open interest, or liquidation evidence without the corresponding data.

## Market Profile / Auction rules

Any operational Market Profile rule must declare:

- TPO/time or volume-based construction;
- session boundaries and timezone/DST policy;
- profile aggregation method;
- exact POC/Value Area algorithm when used;
- acceptance/rejection measurement window and threshold;
- data semantics, especially when broker tick volume is used.

## RTM / discretionary structure rules

A visual term is not machine-ready until swing segmentation, reference-point selection, confirmation timing, invalidation, ties, nested structures, and closed/forming-bar handling are explicit. A native definition may remain `defined` indefinitely if those choices are not source-resolved.

## No hindsight rule

A rule may not use information unavailable at the decision timestamp. Future pivots, centered windows, negative shifts, later-session extrema, or retrospective range labels are prohibited unless they are used only for ex-post research labels and are explicitly isolated from signal generation.

## Registry

`knowledge/OPERATIONALIZATION_REGISTRY.yaml` records current readiness assessments and blockers. A `machine_ready: true` record must satisfy the validator and link to a candidate rule/spec artifact before promotion.
