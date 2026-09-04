# Data Schema Requirements

Every market dataset entering this project should have a companion manifest with these fields.

## Identity

- `dataset_id`
- `instrument`
- `provider`
- `source_file_or_url`
- `retrieved_at`

## Time

- `timezone`
- `timestamp_format`
- `start_timestamp`
- `end_timestamp`
- `cutoff_timestamp`
- `dst_rule`

## Market fields

- `open/high/low/close` availability
- `bid/ask/last` availability
- `volume_type`: real / tick / unavailable
- `spread` availability
- `digits`
- `tick_size`

## Quality

- row count
- missing timestamp count
- duplicate count
- non-monotonic timestamps
- invalid OHLC rows
- forming-candle policy
- resampling method

## Execution assumptions for backtest

- commission
- spread model
- slippage model
- fill timing
- order type
- position sizing

A dataset is not eligible for a reproducible backtest until its manifest is complete enough to reconstruct these assumptions.
