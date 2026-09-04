# Dealer / Market Microstructure — Concept Formalization Ledger

**Current state:** `source_indexed`

Canonical academic source ids:

- `kyle_1985`
- `glosten_milgrom_1985`
- `ho_stoll_1981`
- `grossman_miller_1988`
- `arxiv_2003_05958`
- `arxiv_2407_17393`

## Evidence boundary

This framework may support theoretical concepts such as informed trading, adverse selection, inventory risk, liquidity provision and market making. It does **not** reveal a live dealer/bank inventory state from price candles alone.

No claim about current hidden orders, DOM, CVD, Open Interest, liquidations or dealer inventory is permitted unless the required live data source is actually supplied.

## Concept record schema

```yaml
concept_id:
concept_name:
framework: dealer_microstructure
source_id:
source_locator:
source_state: source_indexed|source_noted|defined|operational_candidate|operational|backtest_ready|validated|rejected_or_unresolved
source_summary:
model_assumptions: []
observable_variables: []
latent_variables: []
data_requirements: []
operational_proxy:
proxy_limitations: []
quant_mapping:
backtest_requirements: []
```

## Operationalization rule

A theoretical variable that is not observable in the available market data must remain latent. If a proxy is proposed, the proxy must be labelled as an interpretation and separately validated.

## Current operational mappings

None yet promoted under the current ingestion protocol.
