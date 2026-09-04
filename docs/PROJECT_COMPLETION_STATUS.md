# Project Completion Status

**Status date:** 2026-09-04  
**Canonical source:** `docs/resource-connector-map.md`

## Executive status

The repository is **operationally complete as a research core**: it can register sources, validate data, create provenance manifests, qualify multi-timeframe OHLC/tick bundles, audit common lookahead patterns, define/freeze strategy specifications, summarize backtest trade results, and expose compact curated artifacts for retrieval.

Framework ingestion and operationalization governance are active under `docs/FRAMEWORK_INGESTION_PROTOCOL.md`, `knowledge/CONCEPT_REGISTRY.yaml`, `docs/OPERATIONALIZATION_GATE.md`, and `knowledge/OPERATIONALIZATION_REGISTRY.yaml`. Native-framework isolation prevents unverified cross-framework substitutions from becoming project truth.

The first operational rule remains `amt_tpo_profile_core_v1`, a deterministic descriptive time-at-price occupancy engine. It is explicitly a project operational interpretation and does not define canonical POC, Value Area, initiative/responsive behavior, or a trading signal.

The XAUUSD timebase blocker has been removed for the new canonical UTC bundle `xauusd_o_utc_20260904_052959`. The export run directly binds UTC timestamp semantics, LiteFinance broker/server identity, terminal metadata, symbol specification, cutoff and per-file SHA-256 values. This does **not** retroactively verify the older source-local bundle.

A named-session context layer is operational under `docs/NAMED_SESSION_POLICY_PROTOCOL.md`, `config/session-policies/xauusd-major-sessions.yaml`, and `research_core/session_policy.py`. The downstream dataset-selection layer is also operational under `docs/NAMED_SESSION_DATASET_PROTOCOL.md` and `research_core/named_session_dataset.py`, with explicit `complete_only`, `allow_incomplete_with_flag`, and coverage-edge handling. These research sessions remain separate from ICT kill zones and strategy logic.

The first frozen downstream study is `xauusd_named_session_tpo_descriptive_v1` in `quant/studies/XAUUSD_NAMED_SESSION_TPO_DESCRIPTIVE_V1.yaml`. Its canonical external-data execution has now been completed and compactly recorded in `quant/results/XAUUSD_NAMED_SESSION_TPO_DESCRIPTIVE_V1.result.yaml`, with a human-readable result report under `data/reports/XAUUSD_o_UTC_20260904_052959.named-session-tpo-study-v1.md`. A dedicated result validator prevents the compact record from drifting away from the frozen study specification.

The repository is **not historically complete** because several pre-existing artifacts named by the canonical map have not been supplied. Those items cannot be reconstructed by inference without contaminating provenance.

## Completion matrix

| Area | Operational infrastructure | Source/content completeness |
|---|---:|---:|
| Canonical architecture | COMPLETE | COMPLETE |
| Source registry & policy | COMPLETE | COMPLETE for mapped source metadata |
| Framework ingestion protocol | COMPLETE | ACTIVE — source-faithful ingestion ongoing |
| Concept registry / definition gate | COMPLETE | PARTIAL — source-supported definitions only |
| Operationalization gate | COMPLETE | ACTIVE — first operational rule admitted after implementation audit |
| ICT/SMC/Wyckoff framework | COMPLETE shell + rule ledger | PARTIAL — official scope notes exist; detailed rule extraction pending |
| RTM framework | COMPLETE shell + rule ledger | PARTIAL — valid-swing definition captured; FTR/BSZ/MPL/Quasimodo/Compression rules pending; `rtm-fshcd` missing |
| Dealer microstructure | COMPLETE shell + definition layer | PARTIAL — theory concepts defined; observable proxies not frozen |
| Auction Market Theory | COMPLETE shell + definition + operational layer | PARTIAL — TPO occupancy engine operational; canonical POC/Value Area/initiative-responsive formulas pending |
| XAUUSD data layer | COMPLETE | canonical UTC bundle qualified for timebase and multi-timeframe price research, with tick-history warnings |
| Timebase qualification | COMPLETE gate + validator | VERIFIED for `xauusd_o_utc_20260904_052959` |
| Named-session policy | COMPLETE engine + validator + CI gate | OPERATIONAL for Asia-Tokyo/London/New York research convention on verified UTC data |
| Named-session dataset adapter | COMPLETE | OPERATIONAL with complete/incomplete/coverage-edge classification and TPO integration |
| Named-session real-data audit | COMPLETE | VERIFIED on canonical M5; sample completeness differs materially by session |
| TPO dataset adapters | COMPLETE | neutral source-day and canonical named-session smoke tests both verified descriptively |
| Descriptive study specification gate | COMPLETE validator + CI gate | FIRST FROZEN SPEC registered for named-session TPO |
| Descriptive study result gate | COMPLETE validator + CI gate | FIRST COMPACT RESULT recorded and internally bound to frozen spec |
| Named-session TPO aggregate study | COMPLETE runner | EXECUTED on canonical external M5; descriptive result recorded |
| MTF qualification engine | COMPLETE | VERIFIED on legacy and canonical H1/M15/M5 bundles |
| Iran-gold data layer | COMPLETE | `general-platforms` sample/spec still missing |
| Quant research workflow | COMPLETE | STRATEGY-DEPENDENT |
| Lookahead/repainting audit tooling | COMPLETE | Static audit only; code-specific review still required |
| Curated RAG artifacts | COMPLETE as generated baseline | Historical originals missing |

## Canonical UTC XAUUSD milestone

Reviewed dataset: `xauusd_o_utc_20260904_052959`.

Records:

- manifest: `data/manifests/XAUUSD_o_UTC_20260904_052959.json`
- qualification report: `data/reports/XAUUSD_o_UTC_20260904_052959.qualification.md`
- exporter protocol: `docs/MT5_UTC_EXPORT_PROTOCOL.md`

Bound identity:

- broker: `LiteFinance Global LLC`
- server: `LiteFinance-MT5-Live`
- timestamp semantics: `utc_from_metatrader5_python_api`
- digits: `2`
- point/tick size: `0.01`
- tick value: `1.0`
- contract size: `100`

H1/M15/M5 bars have zero duplicate timestamps, zero out-of-order rows and zero OHLC integrity errors. Cross-timeframe reconstruction is exact on all complete compared groups:

- M5 → M15: `11,724 / 11,724`
- M5 → H1: `2,911 / 2,911`
- M15 → H1: `2,937 / 2,937`

The two-day BID tick overlap is price-consistent with one preserved warning at `2026-09-04 01:00 UTC`: high/low/close match the rate bars, but the first returned BID tick is `4473.78` while the exported bar open is `4474.40`. Raw tick-record count also differs from bar `tick_volume` in a subset of intervals, so those two quantities are not treated as semantically interchangeable.

**Verdict:** `UTC-TIMEBASE-VERIFIED; MULTI-TIMEFRAME-PRICE-QUALIFIED; TICK-RECONSTRUCTION-WITH-WARNINGS`.

## Named-session milestone

Operational policy:

- `Asia / Tokyo`: `Asia/Tokyo`, 09:00–18:00 local
- `London`: `Europe/London`, 08:00–17:00 local
- `New York`: `America/New_York`, 08:00–17:00 local
- membership: bar-open timestamp, start-inclusive/end-exclusive
- DST: resolved by IANA timezone data, not fixed UTC offsets
- overlaps: preserved
- methodology boundary: these are major-hub research sessions, not ICT kill zones

The deterministic test suite verifies winter/summer UTC shifts and the temporary US/UK DST mismatch period.

Canonical M5 per-instance coverage audit is recorded in `data/reports/XAUUSD_o_UTC_20260904_052959.named-sessions.md`:

- Asia/Tokyo: 128 fully evaluable windows; 12 complete, 116 incomplete, plus 2 coverage edges;
- London: 129 evaluable; 128 complete, 1 incomplete;
- New York: 129 evaluable; 126 complete, 3 incomplete.

Missing bars do not move session boundaries and no holiday explanation is inferred without separate calendar evidence. Future backtests default to `complete_only` unless the frozen Strategy Specification states otherwise.

## Named-session dataset / TPO milestone

`research_core/named_session_dataset.py` converts canonical verified-UTC OHLC data into explicit session instances and preserves the distinction between complete, incomplete and coverage-edge observations.

Selection policies:

- `complete_only` — project default for future backtests;
- `allow_incomplete_with_flag` — diagnostic/descriptive retention with exact missing-bar metadata;
- coverage edges excluded by default.

The real-data smoke test is recorded in `data/reports/XAUUSD_o_UTC_20260904_052959.named-session-tpo.md`. Using canonical M5, cutoff `2026-09-04T05:29:59.763793Z`, and the bound XAUUSD_o tick size `0.01`, the latest complete instances profiled were:

- `asia_tokyo:2026-03-27` — 108 bars, observed 4375.58–4475.04;
- `london:2026-09-03` — 108 bars, observed 4418.79–4495.23;
- `new_york:2026-09-03` — 108 bars, observed 4419.06–4510.78.

These are descriptive occupancy profiles only. No POC, Value Area, trading signal or profitability claim is derived. The small Tokyo complete-session sample relative to London/New York is retained as a material study-design constraint.

## Frozen descriptive-study milestone

Frozen specification: `quant/studies/XAUUSD_NAMED_SESSION_TPO_DESCRIPTIVE_V1.yaml`.

The study is deliberately descriptive rather than a strategy/backtest. It freezes:

- dataset `xauusd_o_utc_20260904_052959`, M5, canonical UTC cutoff;
- named-session policy `xauusd_major_fx_sessions_v1`;
- `complete_only` with coverage edges excluded;
- operational input `amt_tpo_profile_core_v1` at `0.01` price increment;
- permitted features: `range_ticks`, `occupied_bins`, `occupancy_events`, `mean_bin_occupancy`, `bars_seen`;
- summaries: n/min/q25/median/q75/max/mean;
- London and New York as the primary descriptive pair with minimum `n=30` each;
- Asia/Tokyo as secondary descriptive context because the current complete sample is small;
- median difference and left/right median ratio only;
- no significance test, no post-result parameter tuning, no hypothesis rewrite;
- no POC/Value Area, ICT kill-zone substitution, trading signal, profitability, centralized-volume or dealer-inventory claim.

The repository validator `tools/validate_study_specs.py` is part of CI. `research_core/tpo_study.py` and `tools/run_named_session_tpo_study.py` implement the frozen study without changing those rules.

## Recorded descriptive result milestone

Compact result: `quant/results/XAUUSD_NAMED_SESSION_TPO_DESCRIPTIVE_V1.result.yaml`.  
Report: `data/reports/XAUUSD_o_UTC_20260904_052959.named-session-tpo-study-v1.md`.

The local canonical execution passed the sample-size gate with London `n=128` and New York `n=126`; Tokyo had only `n=12` complete sessions and remains secondary descriptive context.

Primary aggregate medians:

- London range: `5,455.5` ticks; New York range: `6,261.5` ticks;
- London occupancy events: `54,008`; New York occupancy events: `65,066`;
- London mean-bin-occupancy: `10.2916`; New York: `10.3821`;
- both primary sessions contain 108 closed M5 bars per complete session.

Therefore New York has the larger aggregate median range and total occupancy-event count in this dataset, while median occupancy density per occupied bin is nearly the same. The study intentionally performs no statistical-significance test and does not establish persistence, causality, prediction, trading edge or profitability.

The compact result is now governed by `research_core/study_result_validation.py` and `tools/validate_study_results.py`; the validator checks binding to the frozen spec, sample-count consistency, primary eligibility and recomputes the recorded median differences/ratios from the recorded session medians.

## Legacy source-local bundle boundary

The older `xauusd_o_mtf_20260903_0922` remains a `candidate` timebase because its original export metadata was not captured. The new UTC bundle is a separate verified dataset and does not alter the historical truth status of the old files.

## First operational rule

`amt_tpo_profile_core_v1` is implemented in `research_core/tpo_profile.py` and frozen in `quant/operational/AMT_TPO_PROFILE_CORE.yaml`.

The implementation enforces closed bars only, forming-bar no-op behavior, externally supplied session IDs, Decimal/integer-tick normalization, strict timestamp ordering, incomplete-session marking on upstream gaps, and no POC/Value Area/entry/exit/centralized-volume/dealer-inventory claims.

## Current blocked areas

- RTM valid swing remains blocked by unresolved objective swing segmentation, termination, tie/nesting, timeframe and forming-bar rules.
- Dealer/microstructure concepts remain blocked until measurable observable proxies and lag/sampling policies are frozen.
- AMT acceptance/rejection remains blocked until measurement window, threshold and confirmation rules are source-frozen.
- Named-session context and dataset construction are operational, but methodology-specific ICT kill zones remain separate and source-extraction work is still required.
- TPO remains descriptive; POC/Value Area and any trading interpretation require separately sourced/frozen operational rules.
- The aggregate London/New York descriptive difference is not yet time/regime-robustness qualified.
- Long-history transaction-cost backtesting still requires a frozen historical spread/slippage/fill model; two-day BID/ASK ticks do not by themselves qualify 180 days of execution costs.

## Hard blockers that cannot be solved by inference

- original `glossary.md`
- original compact `SKILL.md` described by the map as “6-layer + verdict”
- original `MARKET_PARAMS.md`
- `rtm-fshcd`
- `smcp-v3-architecture`
- `quant-engine-9phase`
- BTMM/MMXM/London Close/Choch Plan/1AM CRT translated assets
- inventory of the referenced translated PDF collection
- a real `general-platforms` CSV sample/specification
- exact code/commit for the historical `rolling(center=True)` correction
- historical Strategy Specifications and backtest outputs referenced by those internal systems

Generated equivalents exist where useful, but they are explicitly labelled generated and do not satisfy historical recovery.

## Current next workstream

1. freeze and execute a temporal/regime robustness study for the same London/New York descriptive features without changing V1 definitions;
2. report monthly/period-slice stability and sample sizes before any attempt to convert the aggregate difference into a hypothesis;
3. keep ICT kill zones separate until their own official-source boundaries are extracted and frozen;
4. continue authoritative framework source extraction and operationalization independently;
5. define POC/Value Area only after an authoritative source and exact algorithm are frozen;
6. create a Strategy Specification only when an actual entry/exit hypothesis, execution model, costs, IS/OOS, lookahead and robustness controls are explicit.

## Quality gate

No missing historical item is required to use the repository for new research. It is required only when a claim depends on that historical artifact.
