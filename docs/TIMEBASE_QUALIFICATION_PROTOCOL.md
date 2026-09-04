# Timebase Qualification Protocol

## Purpose

Prevent source-local market timestamps from being silently relabelled as UTC, broker-server time, Tehran time, or named trading sessions.

This protocol controls promotion of a dataset from an unresolved source clock to a timebase that is safe for session-sensitive research.

## Status states

- `unresolved` — source timestamps are internally usable, but timezone/DST semantics are not established.
- `candidate` — one or more credible timebase mappings exist, but independent confirmation is incomplete.
- `verified` — source timezone and DST/session-clock policy are supported by sufficient provenance for named-session use.

A dataset may be structurally qualified while its timebase remains `unresolved`.

## Evidence classes

Timebase evidence must be classified explicitly:

- `direct_source_metadata` — timezone/offset recorded by the export, terminal, API, or machine-readable provider metadata.
- `broker_documentation` — provider documentation that explicitly states the server/data clock and DST policy applicable to the dataset.
- `terminal_observation` — recorded terminal clock compared against a trusted UTC clock at the same observation instant.
- `controlled_crosscheck` — timestamped source event matched to an independently timestamped external reference with a documented method.
- `statistical_inference` — recurring gaps, day boundaries, candle alignment, or event coincidences used only as supporting inference.

Statistical inference alone can never promote a dataset to `verified`.

## Verification requirements

`verified` requires all of the following:

1. explicit `source_timezone` or fixed UTC offset semantics;
2. explicit `dst_policy` (`none`, named timezone rules, or a documented broker-specific schedule);
3. broker/feed identity sufficient to bind the policy to the source;
4. at least one non-statistical evidence item;
5. no unresolved contradiction between evidence items;
6. a provenance record identifying when and how the evidence was captured.

## Named-session gate

London, New York, Asia, CME/exchange, kill-zone, or other named-session classification is prohibited unless `named_session_use_allowed: true`.

That flag may be true only for a `verified` timebase. Session definitions themselves must also be frozen separately; verified timezone does not automatically define a trading methodology's session windows.

## Candidate use

A `candidate` mapping may be used for sensitivity analysis only. Results must be labelled with the candidate timebase and repeated under plausible alternatives when the offset could affect conclusions.

Candidate mappings cannot be used to make definitive session-performance, kill-zone, session-high/low, or DST-sensitive claims.

## Unresolved use

When status is `unresolved`, allowed operations include:

- timestamp ordering;
- closed/forming-bar determination relative to an explicit cutoff expressed in the same source clock;
- cross-timeframe aggregation on the same source clock;
- neutral technical grouping such as `source_calendar_day_v1`;
- price-only research that does not depend on named sessions.

Prohibited operations include converting the clock to UTC/Tehran/New York/London by assumption or assigning named-session semantics.

## Required registry fields

Each tracked dataset/bundle must record:

- `dataset_id`
- `source_id`
- `status`
- `source_timestamp_semantics`
- `source_timezone`
- `dst_policy`
- `broker_feed_identity`
- `named_session_use_allowed`
- `neutral_policy` when unresolved
- `evidence`
- `blockers`

## XAUUSD current rule

The current `XAUUSD_o` qualified bundle remains source-local with unresolved timezone/DST semantics. Exact cross-timeframe and tick-to-bar price reconstruction does not prove timezone. Repeated daily/weekly gaps may be useful evidence for later investigation but are not timezone proof.
