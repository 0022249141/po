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

## Multi-timeframe qualified bundle

The first cross-timeframe qualification bundle is:

`xauusd_o_mtf_20260903_0922`

It contains H1, M15, M5 and tick exports with operational cutoff `2026-09-03 09:22:00.092` source-local.

Records:

- bundle manifest: `data/manifests/XAUUSD_o_MTF_20260903_0922.json`
- qualification report: `data/reports/XAUUSD_o_MTF_20260903_0922.qualification.md`
- individual H1/M15/M5/Tick manifests under `data/manifests/`

Cross-timeframe result:

- M5 → M15: 10,730 complete groups, 0 OHLC mismatches
- M5 → H1: 2,664 complete groups, 0 OHLC mismatches
- M15 → H1: 2,688 complete groups, 0 OHLC mismatches
- Tick BID → M5: 160 completed bars, 0 OHLC mismatches
- Tick BID → M15: 53 completed bars, 0 OHLC mismatches
- Tick BID → H1: 13 completed bars, 0 OHLC mismatches

One retained warning exists: M5 `2026-09-03 07:10` reports `TICKVOL=917` while the companion tick export contains 915 records in that interval. OHLC is still exact; the discrepancy is not silently explained away.

At the bundle cutoff the H1 09:00, M15 09:15 and M5 09:20 rows are forming and are excluded from close-confirmed logic.

**Current qualification:** `multi-timeframe-qualified-price-data-with-warnings`.

Timezone/DST, broker/feed identity and exact symbol contract metadata are still required before session-sensitive or fully cost-qualified backtesting.

## Operational TPO real-data smoke test

The first operational framework engine applied to real XAUUSD data is `amt_tpo_profile_core_v1` through the neutral source-day adapter:

- engine: `research_core/tpo_profile.py`
- adapter: `research_core/tpo_dataset_adapter.py`
- session policy: `config/session-policies/source-calendar-day.yaml`
- CLI: `tools/run_source_day_tpo.py`
- report: `data/reports/XAUUSD_o_M5_20260903.source-day-tpo.md`

Input: `XAUUSD_o_M5_202603230005_202609030920.csv`, SHA-256 `9503650ad91aa96aaf6cf921f48f457c55b974bd49ef9760412a9b77a1730452`.

Using the already-qualified cutoff `2026-09-03 09:22:00.092` and an explicitly declared research profile increment of `0.10`, the current technical source-day group contains 100 closed M5 bars from 01:00 through 09:15. The 09:20 bar is forming and contributes zero occupancy. No internal five-minute gaps occur inside the observed 01:00–09:15 segment.

This is a **technical source-calendar-date grouping only**. It is not a London, New York, Asia, exchange, broker-business-day, or canonical Market Profile session. No timezone/DST inference is performed. The result is descriptive occupancy only and does not create POC, Value Area, entry/exit, or profitability claims.

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

Dukascopy is intended as an independent historical benchmark against broker/MT5 data. Differences between feeds must be measured rather than assumed negligible.

The first MT5-derived M5 dataset is approved for **price-based research with warnings**, not yet for timezone-sensitive session research or fully qualified transaction-cost backtesting. The multi-timeframe bundle adds exact internal aggregation and tick/BID OHLC reconstruction evidence but does not remove the unresolved timezone/source/contract blockers.

The TPO source-day smoke test proves deterministic real-data execution of one descriptive operational rule. It does not promote the XAUUSD dataset to named-session backtest readiness.

## TradingView role

TradingView is a chart/visual and implementation cross-check layer in this architecture. A community script does not constitute validation of a trading concept.
