# ICT / SMC / Wyckoff — Rule Formalization Ledger

**Current state:** `source_indexed`  
**Authority:** sources registered under `ict_official_youtube`, `ict_official_x`, `wyckoff_analytics`, and `ggu_fi354`.

This file is intentionally a formalization ledger, not a reconstructed course. A rule is added only after source-faithful ingestion.

## Rule record schema

For every concept/rule:

```yaml
concept_id:
concept_name:
framework: ict_smc_wyckoff
source_id:
source_locator:
source_state: source_indexed|source_noted|defined|operational_candidate|operational|backtest_ready|validated|rejected_or_unresolved
source_summary:
ambiguities: []
data_requirements: []
lookback:
reference_set:
trigger:
confirmation:
invalidation:
entry_timing:
exit_or_target:
forming_bar_policy:
timezone_dependency:
missing_data_policy:
edge_cases: []
interpretation_notes: []
quant_spec_path:
```

## Isolation rule

Do not use RTM, Dealer/Microstructure, or Auction Market Theory terminology to fill a missing ICT/SMC/Wyckoff definition. Cross-framework equivalence is never assumed.

## Current operational rules

None yet promoted from the authoritative sources under the current ingestion protocol.
