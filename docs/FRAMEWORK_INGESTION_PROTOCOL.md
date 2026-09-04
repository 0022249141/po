# Framework Knowledge Ingestion Protocol

## Purpose

This protocol governs how ICT/SMC/Wyckoff, RTM, Dealer/Market Microstructure, and Auction Market Theory content enters the repository.

The goal is source-faithful knowledge that can later be operationalized and backtested without silently mixing frameworks or inventing missing rules.

## Ingestion states

Every concept must have exactly one state:

- `source_indexed` — authoritative source identified; content not yet normalized.
- `source_noted` — source-faithful note exists with provenance.
- `defined` — native-framework definition recorded without cross-framework substitution.
- `operational_candidate` — definition can plausibly be translated into explicit variables/conditions, but has not passed rule audit.
- `operational` — lookback, trigger, confirmation, invalidation, timing and data requirements are explicit enough to implement without visual hindsight.
- `backtest_ready` — operational rule has a frozen Strategy Specification and implementation boundary.
- `validated` — backtest/robustness evidence exists in the Quant layer.
- `rejected_or_unresolved` — source conflict, insufficient evidence, or unresolvable discretion prevents promotion.

## Mandatory evidence fields

Each source-derived note must record:

1. `framework`
2. `concept_id`
3. `concept_name`
4. `source_id` from `config/source-registry.yaml`
5. exact source locator (URL, document, chapter/page, video + timestamp, repository path/commit)
6. source date/version when available
7. source class
8. source-faithful summary
9. direct quotation only when legally/operationally necessary and within citation limits
10. ambiguities / unresolved terms
11. data requirements
12. current ingestion state

## Native-framework isolation rule

A concept must first be defined inside its own framework.

Examples:

- RTM FTR is not to be defined by importing ICT order-block terminology.
- ICT FVG is not to be defined from a community SMC script unless explicitly labelled as an implementation cross-check.
- Dealer inventory theory is not evidence of a current bank inventory state.
- Auction Market Theory Value Area / POC is not interchangeable with an ICT dealing range unless a later crosswalk explicitly states the interpretation.

Cross-framework mappings belong only in a dedicated `crosswalk.md` after both source-side definitions exist independently.

## Operationalization gate

A rule cannot become `operational` until all of the following are explicit:

- instrument/data type
- timeframe or event clock
- lookback / reference-set construction
- state variables
- trigger
- confirmation rule
- invalidation rule
- entry timing if applicable
- exit/target rule if applicable
- forming-vs-closed-bar policy
- tie/edge-case handling
- missing-data behavior
- timezone/session dependency where relevant

Anything still dependent on visual hindsight remains `defined` or `operational_candidate`.

## Observed vs interpreted vs tested

Every artifact must keep these layers separate:

- **Observed/source statement** — what the authoritative source actually states.
- **Interpretation** — our structured reading or mapping.
- **Operational rule** — explicit machine-testable specification.
- **Backtested evidence** — empirical result from the Quant layer.

No backtest metric is written into framework definitions as if it were source truth.

## Source hierarchy

1. primary/official practitioner or original academic source
2. official education / exchange material
3. user-provided original project artifact with provenance
4. implementation/reference source
5. community code only as cross-check

A lower-level source may not silently override a higher-level definition.

## Promotion control

Promotion between states requires an artifact update with provenance. A concept may move backward if later evidence reveals ambiguity, leakage, or source conflict.

## No-fabrication rule

If the source is inaccessible, missing, or ambiguous, record the missing dependency. Do not create a plausible definition and label it canonical.
