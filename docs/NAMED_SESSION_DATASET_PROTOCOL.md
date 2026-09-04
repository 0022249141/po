# Named-Session Dataset Protocol

**Status:** operational for canonical verified-UTC OHLC data.

## Purpose

Define how a verified-UTC OHLC dataset is converted into deterministic named-session instances before descriptive analysis or backtesting. This protocol separates session membership from data completeness and prevents missing feed data from silently changing session boundaries.

Implementation:

- session policy: `config/session-policies/xauusd-major-sessions.yaml`
- classifier: `research_core/session_policy.py`
- dataset adapter: `research_core/named_session_dataset.py`
- CLI: `tools/run_named_session_tpo.py`
- canonical XAUUSD coverage audit: `data/reports/XAUUSD_o_UTC_20260904_052959.named-sessions.md`
- named-session TPO smoke test: `data/reports/XAUUSD_o_UTC_20260904_052959.named-session-tpo.md`

## Input requirements

The adapter requires:

1. timezone-aware timestamps with verified UTC semantics;
2. a supported bar timeframe;
3. an explicit timezone-aware cutoff;
4. a separately validated named-session policy;
5. strictly increasing bar-open timestamps;
6. closed/forming status derived causally from `bar_open + timeframe <= cutoff`.

Canonical MT5 files may expose UTC time as `time_utc` or `timestamp_utc`. Naive timestamps are rejected for named-session use.

## Session membership

Membership is delegated to `NamedSessionPolicy` and therefore inherits the frozen policy rules:

- IANA timezone identifiers;
- DST from the timezone database;
- fixed UTC offsets prohibited;
- start-inclusive/end-exclusive windows;
- overlaps allowed;
- no holiday inference from missing bars;
- missing data never shifts the session window;
- major-hub research sessions are not ICT kill zones.

## Session instances

Each session instance is identified as:

`<session_id>:<local-start-calendar-date>`

For every eligible local date, the adapter calculates the exact UTC start/end bounds and the full set of expected bar-open timestamps for the requested timeframe.

An instance is then classified as one of:

- **complete** — every expected bar open is present and the full session lies inside dataset coverage;
- **incomplete** — the full session is evaluable but one or more expected bar opens are absent;
- **coverage edge** — the session starts before the dataset begins or ends after the explicit cutoff.

A zero-bar fully evaluable instance remains an incomplete session. It is not discarded as if the session never existed.

## Selection policies

### `complete_only`

Project default for future backtests unless a frozen Strategy Specification states otherwise.

- include only complete session instances;
- exclude incomplete instances;
- exclude coverage edges by default.

### `allow_incomplete_with_flag`

Diagnostic/descriptive mode.

- retain fully evaluable incomplete sessions;
- report expected, observed and missing bar counts;
- preserve exact missing bar-open timestamps;
- mark the downstream TPO profile as incomplete.

### Coverage-edge handling

`exclude_coverage_edges = true` is the project default.

Coverage edges may be retained only for diagnostics. They must not be treated as complete-session observations.

## TPO application

When `amt_tpo_profile_core_v1` is applied through the named-session adapter:

- only closed bars are passed to the TPO engine;
- `session_instance_id` is supplied externally by the session layer;
- the explicit price increment is recorded;
- missing expected bars create an incomplete-profile flag;
- no POC, Value Area, initiative/responsive, entry/exit or profitability rule is created.

For `XAUUSD_o`, the canonical bundle binds a trade tick size of `0.01`; using `0.01` as the TPO price increment is therefore instrument-metadata-supported for that dataset.

## Canonical XAUUSD default

For `xauusd_o_utc_20260904_052959`:

- timeframe: `M5` for the current session-coverage evidence;
- cutoff: `2026-09-04T05:29:59.763793Z`;
- session policy: `xauusd_major_fx_sessions_v1`;
- price increment: `0.01`;
- completeness policy: `complete_only`;
- coverage edges: excluded.

The canonical coverage audit shows material sample-size asymmetry: Tokyo has far fewer complete instances than London/New York. Cross-session studies must report that asymmetry rather than assuming equal observation quality.

## Boundary of evidence

This protocol authorizes deterministic session-conditioned dataset construction. It does **not** establish:

- a trading edge;
- ICT kill-zone equivalence;
- canonical Market Profile POC or Value Area formulas;
- holiday/early-close causes;
- centralized exchange volume, DOM, CVD or open interest;
- dealer inventory or bank positioning;
- transaction-cost realism beyond separately frozen execution assumptions.

## Promotion rule

A named-session result may enter a backtest only after the Strategy Specification freezes:

- permitted session ids;
- completeness policy;
- coverage-edge policy;
- allowed descriptive features;
- signal timing and closed-bar policy;
- execution/fill/cost model;
- IS/OOS and robustness procedure.
