# XAUUSD Data

## Sources named by the canonical map

- **Dukascopy** — historical tick/minute data for parallel backtesting.
- **MT5 exports** — user-provided operational market data when supplied.
- **TradingView** — visual cross-check and community-script implementation review.
- **TradingEconomics / ForexFactory** — macro-event metadata for Time Logic / Volatility State.

## Data roles

These sources are not interchangeable. Every analysis/backtest must state which provider generated the data and must not splice providers without an explicit normalization step.

## First canonical ingest

The first real dataset registered under the current repository architecture is:

`XAUUSD_o_M5_202503210000_202609031255.csv`

Repository records:

- manifest: `data/manifests/XAUUSD_o_M5_202503210000_202609031255.json`
- validation report: `data/reports/XAUUSD_o_M5_202503210000_202609031255.validation.md`
- source id: `user_mt5_export`

It contains 103,037 M5 rows from `2025-03-21 00:00:00` through `2026-09-03 12:55:00` in unresolved source-local time. Structural OHLC/timestamp checks pass with gap warnings. The final 12:55 row is not accepted as a closed candle until the export cutoff is proven.

## Legacy multi-timeframe qualified bundle

The first cross-timeframe qualification bundle is:

`xauusd_o_mtf_20260903_0922`

It contains H1, M15, M5 and tick exports with operational cutoff `2026-09-03 09:22:00.092` source-local.

Records:

- bundle manifest: `data/manifests/XAUUSD_o_MTF_20260903_0922.json`
- qualification report: `data/reports/XAUUSD_o_MTF_20260903_0922.qualification.md`

Cross-timeframe and BID-tick reconstruction are internally strong, but this legacy bundle retains unresolved original-export timebase/source binding. It remains useful for price research and is not retroactively relabelled as canonical UTC.

## Canonical UTC multi-timeframe bundle

The first provenance-bound UTC dataset is:

`xauusd_o_utc_20260904_052959`

Records:

- reviewed manifest: `data/manifests/XAUUSD_o_UTC_20260904_052959.json`
- qualification report: `data/reports/XAUUSD_o_UTC_20260904_052959.qualification.md`
- timebase registry: `config/timebase/XAUUSD_o.yaml`
- exporter protocol: `docs/MT5_UTC_EXPORT_PROTOCOL.md`

The export binds the data to:

- `LiteFinance Global LLC / LiteFinance-MT5-Live`
- `utc_from_metatrader5_python_api`
- digits `2`
- point/tick size `0.01`
- tick value `1.0`
- contract size `100`

Coverage:

- H1: 2,940 rows
- M15: 11,753 rows
- M5: 35,229 rows
- Tick: 655,779 rows over the final two-day window

All H1/M15/M5 files contain zero duplicate timestamps, zero out-of-order rows and zero OHLC integrity errors. Exact complete-group reconstruction:

- M5 → M15: 11,724 / 11,724 exact OHLC and summed bar tick-volume
- M5 → H1: 2,911 / 2,911 exact
- M15 → H1: 2,937 / 2,937 exact

Tick BID reconstruction is exact for 550/551 M5 bars, 182/183 M15 bars and 44/45 H1 bars. The single underlying mismatch is the `2026-09-04 01:00 UTC` bar open; high/low/close still match. Raw tick-record counts also differ from bar `tick_volume` in a subset of intervals, so those fields are not treated as semantically identical.

**Current qualification:** `UTC-TIMEBASE-VERIFIED; MULTI-TIMEFRAME-PRICE-QUALIFIED; TICK-RECONSTRUCTION-WITH-WARNINGS`.

Named-session research is now eligible on this new bundle only after an explicit IANA-timezone/DST-aware session policy is frozen. UTC provenance does not itself define London, New York, Asia or ICT kill-zone boundaries.

## Operational TPO real-data smoke test

The first operational framework engine applied to real XAUUSD data is `amt_tpo_profile_core_v1` through the neutral source-day adapter:

- engine: `research_core/tpo_profile.py`
- adapter: `research_core/tpo_dataset_adapter.py`
- session policy: `config/session-policies/source-calendar-day.yaml`
- CLI: `tools/run_source_day_tpo.py`
- report: `data/reports/XAUUSD_o_M5_20260903.source-day-tpo.md`

The existing smoke test uses the older source-local bundle and remains a technical source-calendar-date grouping only. It proves deterministic engine execution, not named-session semantics. A new named-session application must use the canonical UTC dataset and a separately validated session policy.

## Validation checklist

- symbol/provider identity
- timezone and DST treatment
- digits/tick size
- bid/ask/mid construction
- spread availability
- timestamp cutoff
- closed vs forming bars
- gaps and duplicates
- session boundaries
- resampling method
- transaction-cost assumptions

## Backtest use

Dukascopy remains an intended independent historical benchmark against broker/MT5 data. Differences between feeds must be measured rather than assumed negligible.

The canonical UTC bundle removes the timestamp-timezone and broker/symbol binding blocker for new research. It does **not** by itself provide centralized exchange volume, DOM/CVD, dealer inventory, or a 180-day tick-level execution-cost history. Long-history cost-sensitive testing still requires an explicit spread/slippage/fill model and separate robustness checks.

## TradingView role

TradingView is a chart/visual and implementation cross-check layer in this architecture. A community script does not constitute validation of a trading concept.
