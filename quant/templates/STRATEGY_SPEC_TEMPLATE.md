# Strategy Specification Template

**Spec ID:** `SPEC-...-v1.0`  
**Status:** draft / frozen / superseded  
**Owner:**  
**Frozen at:**

## 1. Research question

What specific edge/hypothesis is being tested?

## 2. Market and data

- market/symbol:
- source/dataset id:
- timeframe(s):
- session/timezone:
- cutoff policy:
- closed/forming-bar policy:

## 3. Definitions

Define every concept operationally. Include swing/pivot/structure/FVG/zone/liquidity rules if used. Mark any remaining subjective element `DISCRETIONARY`.

## 4. Entry

- direction eligibility:
- causal sequence:
- exact trigger:
- order type:
- order timing:
- cancellation condition:

## 5. Invalidation / Stop

- structural or explicit rule:
- price calculation:
- gap/open behavior:

## 6. Exit / Targets

- target rule:
- partial exits:
- time exit:
- trailing rule:

## 7. Sizing and risk

- position sizing:
- max concurrent positions:
- daily/session risk gates:

## 8. Execution model

- commission:
- spread:
- slippage:
- same-bar stop/target priority:
- fill assumptions:

## 9. Parameters

List parameters with fixed baseline values and rationale. Separate structural definitions from tunable parameters.

## 10. Acceptance criteria

Define before final test. Avoid optimizing toward a single metric.

## 11. Change log

Any rule change after freeze creates a new version. Never silently mutate the spec.
