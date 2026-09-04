# `general-platforms` CSV — Provisional Intake Contract

**Not a recovered specification.** The canonical map says this is an existing intraday feed format for Iran-gold work. No real sample is currently in the repository.

## Do not assume

Do not assume it is a trade-history schema (`Side`, `Entry`, `Exit`, P&L). That interpretation was audited as unsupported.

## First-sample procedure

When a real file arrives:

1. preserve original bytes and compute SHA-256;
2. record encoding, delimiter and header names;
3. identify timestamp column(s) and source timezone;
4. identify whether rows are tick, quote, OHLC or another market-data shape;
5. identify symbol/instrument/unit semantics;
6. measure ordering, duplicates and missing intervals where meaningful;
7. distinguish closed vs forming bars if candle data;
8. create `general-platforms-v1.schema.json` only from observed columns;
9. add a small de-identified/approved sample if appropriate;
10. update `config/source-registry.yaml` ingest status from `sample_missing`.
