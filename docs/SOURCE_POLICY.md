# Source & Provenance Policy

## 1. Source hierarchy

Priority order for knowledge ingestion:

1. Original/official source named in the canonical map.
2. Academic paper or exchange/official education source.
3. Direct market/data provider.
4. Community implementation only for code cross-checking, never as authority for a concept.
5. Third-party reposts are excluded when an official source exists.

## 2. Required provenance metadata

Every ingested artifact should record:

- `source_id`
- title / author / organization
- canonical URL or bibliographic reference
- source class
- retrieval date
- publication/version date when available
- language
- processing state: raw / summarized / normalized / operationalized
- copyright handling note
- confidence in source identity

## 3. Separation of evidence classes

Do not merge the following in one statement without labeling:

- **Observed Data** — candles, ticks, prices, timestamps, event records.
- **Source Definition** — what a named source explicitly teaches or defines.
- **Interpretation** — analytical mapping or explanation.
- **Hypothesis** — proposed causal/market logic.
- **Backtested Evidence** — reproducible test results.

## 4. Practitioner frameworks

ICT, RTM, Wyckoff and Auction Market Theory remain separate knowledge domains at ingestion time. A cross-framework equivalence may be written only in a dedicated `crosswalk` artifact and must identify whether the mapping is explicit in sources or an analytical interpretation.

## 5. Academic Dealer/Inventory material

The papers named in the canonical map are used to ground market-microstructure concepts such as inventory risk and informed trading. They must not be used to claim direct visibility into bank inventory, dealer books, DOM, CVD, Open Interest or hidden institutional orders when those data are not available.

## 6. Market data quality

Any dataset used for analysis/backtesting must state at minimum:

- instrument and provider
- timezone
- start/end timestamps
- last valid cutoff
- bar construction
- closed vs forming candle treatment
- missing bars / duplicates
- spread/commission/slippage assumptions where relevant
- whether volume is real, tick volume, or unavailable

## 7. Copyright / source storage

The repository should prefer metadata, short source notes, derived definitions and user-owned/authorized files. Full copyrighted books, paid courses or copied third-party PDFs should not be committed unless the user has a lawful right to store them and explicitly chooses to do so.

## 8. Validation rule

A trading rule is not marked `validated` merely because it appears in a source or code repository. Validation requires a frozen Strategy Specification, implementation audit and reproducible test results.
