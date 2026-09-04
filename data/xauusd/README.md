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

## Named major-hub session policy

The canonical UTC dataset has an explicit, separately validated context policy:

- protocol: `docs/NAMED_SESSION_POLICY_PROTOCOL.md`
- policy: `config/session-policies/xauusd-major-sessions.yaml`
- engine: `research_core/session_policy.py`
- validator: `tools/validate_named_sessions.py`
- coverage audit: `data/reports/XAUUSD_o_UTC_20260904_052959.named-sessions.md`

Research convention:

- Asia/Tokyo — `Asia/Tokyo`, 09:00–18:00 local
- London — `Europe/London`, 08:00–17:00 local
- New York — `America/New_York`, 08:00–17:00 local

DST is resolved from IANA timezone data, not fixed UTC offsets. Session start is inclusive and end is exclusive. Overlaps are preserved. These windows are **not** ICT kill zones and must not be substituted for methodology-specific session rules.

Canonical M5 completeness audit:

- Asia/Tokyo: 128 evaluable full windows; 12 complete, 116 incomplete, plus two coverage-edge instances
- London: 129 evaluable; 128 complete, 1 incomplete
- New York: 129 evaluable; 126 complete, 3 incomplete

Missing bars do not move session boundaries. Holiday or early-close labels are not inferred from absence alone.

## Named-session dataset adapter

The session policy is now connected to a dataset adapter:

- protocol: `docs/NAMED_SESSION_DATASET_PROTOCOL.md`
- adapter: `research_core/named_session_dataset.py`
- CLI: `tools/run_named_session_tpo.py`
- real-data report: `data/reports/XAUUSD_o_UTC_20260904_052959.named-session-tpo.md`

The adapter classifies each session instance independently as:

- `complete`;
- `incomplete` with exact missing bar-open timestamps;
- `coverage_edge` when dataset start/cutoff truncates the window.

Project default for backtest-facing data is `complete_only` with coverage edges excluded. `allow_incomplete_with_flag` is available for diagnostic/descriptive studies and never upgrades an incomplete session to complete.

Canonical M5 named-session TPO smoke test, using the bound XAUUSD_o price increment `0.01`:

| Latest complete instance | Closed M5 bars | Observed low | Observed high |
|---|---:|---:|---:|
| `asia_tokyo:2026-03-27` | 108 | 4375.58 | 4475.04 |
| `london:2026-09-03` | 108 | 4418.79 | 4495.23 |
| `new_york:2026-09-03` | 108 | 4419.06 | 4510.78 |

The Tokyo complete-only sample is materially smaller than London/New York on this feed. Cross-session studies must therefore report sample-size asymmetry and must not assume equal observation quality.

The generated profiles are descriptive time-at-price occupancy only. They do **not** define POC, Value Area, ICT kill zones, entries/exits or profitability.

## Neutral source-day TPO smoke test

The earlier `amt_tpo_profile_core_v1` smoke test remains preserved for the legacy source-local bundle:

- engine: `research_core/tpo_profile.py`
- neutral adapter: `research_core/tpo_dataset_adapter.py`
- neutral session policy: `config/session-policies/source-calendar-day.yaml`
- CLI: `tools/run_source_day_tpo.py`
- report: `data/reports/XAUUSD_o_M5_20260903.source-day-tpo.md`

That test remains a technical source-calendar-date grouping only. Named-session research should use the canonical UTC dataset and the named-session adapter instead.

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
- session completeness
- coverage-edge policy
- resampling method
- transaction-cost assumptions

## Backtest use

Dukascopy remains an intended independent historical benchmark against broker/MT5 data. Differences between feeds must be measured rather than assumed negligible.

The canonical UTC bundle removes the timestamp-timezone and broker/symbol binding blocker for new research. Named-session conditioning is now deterministic, but a backtest still requires a frozen Strategy Specification that selects permitted sessions, completeness policy, execution timing, costs, IS/OOS procedure and robustness criteria.

The canonical bundle does **not** provide centralized exchange volume, DOM/CVD, dealer inventory, or a 180-day tick-level execution-cost history. Long-history cost-sensitive testing still requires an explicit spread/slippage/fill model and separate robustness checks.

## TradingView role

TradingView is a chart/visual and implementation cross-check layer in this architecture. A community script does not constitute validation of a trading concept.
