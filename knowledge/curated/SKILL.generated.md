# Project Capability Profile — Generated

> This is a generated operational capability document. It is **not** the historical `SKILL.md` described by the canonical map as a “6-layer + verdict” artifact.

## 1. Source Governance

Capabilities:
- stable source registry
- primary/official/academic/community classification
- source-role restrictions
- provenance and generated-content labelling
- historical asset recovery protocol

## 2. Knowledge Engineering

Capabilities:
- framework-isolated note structure
- curated retrieval artifacts
- cross-framework boundary rules
- objective vs discretionary tagging
- explicit Source Definition / Interpretation / Hypothesis separation

## 3. Market Data Quality

Capabilities:
- OHLC and tick CSV validation
- timestamp ordering and duplicate checks
- OHLC consistency checks
- bid/ask sanity checks
- gap reporting
- cutoff/forming-bar policy documentation
- SHA-256 dataset provenance manifests

## 4. Strategy Research

Capabilities:
- frozen Strategy Specification template
- explicit entry/exit/invalidation/cancellation definitions
- transaction-cost and fill-model requirements
- versioned experiment logs

## 5. Implementation Audit

Capabilities:
- static warnings for common future-leakage patterns
- centered rolling warning
- negative shift warning
- Pine `lookahead_on` warning
- pivot-confirmation review flags
- reproducible quality-gate workflow

## 6. Backtest Evaluation

Capabilities:
- trade count
- net P&L
- profit factor
- expectancy
- average trade
- average win/loss
- max drawdown
- consecutive losses
- long/short split
- IS/OOS and robustness documentation templates

## Verdict layer

The repository may emit research claim states only:

`idea → specified → implemented → backtested → oos_checked → robustness_checked → validated_for_scope / rejected`

It does not emit certainty, guaranteed profitability, or institutional-order claims without evidence.
