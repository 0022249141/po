# Auction Market Theory / Market Profile — Rule Formalization Ledger

**Current state:** `source_indexed`

Canonical references are the Dalton books and CME education source registered in `config/source-registry.yaml`.

Named concepts from the canonical map: Value Area, POC, Initiative activity, Responsive activity.

## Rule record schema

```yaml
concept_id:
concept_name:
framework: auction_market_theory
source_id:
source_locator:
source_state: source_indexed|source_noted|defined|operational_candidate|operational|backtest_ready|validated|rejected_or_unresolved
source_summary:
profile_input_type:
aggregation_method:
session_definition:
lookback:
trigger:
confirmation:
invalidation:
data_requirements: []
volume_semantics:
edge_cases: []
interpretation_notes: []
quant_spec_path:
```

## Volume/data boundary

Any POC or Value Area computation must record the exact profile input and aggregation method. Broker tick volume must not be relabelled as centralized exchange volume.

## Cross-framework boundary

Do not equate Value Area, POC, initiative/responsive behavior, or auction balance/imbalance with ICT dealing ranges, RTM structures, or dealer inventory variables unless a later crosswalk explicitly documents the interpretation and evidence.

## Current operational rules

None yet promoted from canonical sources under the current ingestion protocol.
