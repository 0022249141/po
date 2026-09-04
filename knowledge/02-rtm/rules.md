# RTM — Rule Formalization Ledger

**Current state:** `source_indexed`  
**Authority:** `readthemarket` and `rtm_academy`.

Named concepts from the canonical map: FTR, BSZ, MPL, Quasimodo, Compression.

No definition below may be filled from ICT/SMC analogies. The missing internal artifact `rtm-fshcd` remains a separate unresolved dependency.

## Rule record schema

```yaml
concept_id:
concept_name:
framework: rtm
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

## Current concept queue

| Concept | State | Note |
|---|---|---|
| FTR | source_indexed | native RTM definition still to be ingested |
| BSZ | source_indexed | native RTM definition still to be ingested |
| MPL | source_indexed | native RTM definition still to be ingested |
| Quasimodo | source_indexed | native RTM definition still to be ingested |
| Compression | source_indexed | native RTM definition still to be ingested |

## Current operational rules

None yet promoted under the current ingestion protocol.
