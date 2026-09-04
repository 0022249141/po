# Temporal Robustness Protocol — Named-Session TPO

## Scope

This protocol governs the declared post-result follow-up study
`xauusd_named_session_tpo_temporal_robustness_v1`.

It does **not** create a trading strategy and does **not** authorize statistical-significance,
predictive, causal, profitability, POC/Value-Area, order-flow, or dealer-inventory claims.

## Why this is a follow-up

The base aggregate study `xauusd_named_session_tpo_descriptive_v1` was already executed before this
robustness specification was frozen. The base result observed higher New York aggregate medians for
`range_ticks` and `occupancy_events` than London. This temporal study therefore declares those
observed directions explicitly and tests whether they persist across time buckets. It must never be
presented as if the directional hypothesis preceded the base result.

## Frozen invariants

The follow-up preserves the base study inputs:

- dataset: `xauusd_o_utc_20260904_052959`;
- timeframe: M5;
- verified UTC timebase and original cutoff;
- named-session policy `xauusd_major_fx_sessions_v1`;
- London and New York research sessions;
- `complete_only` selection;
- coverage edges excluded;
- TPO operational rule `amt_tpo_profile_core_v1`;
- price increment `0.01`;
- closed bars only;
- no significance test.

## Temporal bucket

The unit of temporal robustness is calendar month derived from the **local session start date** encoded
in `session_instance_id`, not from an inferred broker/session timezone.

A monthly bucket is eligible only when both London and New York contain at least `10` complete session
instances in that month.

## Directional persistence outputs

Directional persistence is evaluated only for:

- `range_ticks`;
- `occupancy_events`.

For each eligible month the study records the London/New York medians, left-minus-right difference,
left/right ratio, and direction. It then reports:

- eligible bucket count;
- matching-direction bucket count;
- matching-direction fraction.

The reference direction for both tracked features is `new_york_gt_london`, because that is what the
base recorded result observed. A mismatch is evidence of temporal instability, not a reason to tune
or redefine the study.

## Regime boundary

This version intentionally defines **no volatility, macro-event, trend, or other regime labels**.
Adding a regime classifier would introduce a new conditioning rule and requires a separate frozen
specification after this temporal study is recorded.

## Execution

Run locally against the external canonical M5 CSV:

```powershell
py tools\run_named_session_tpo_temporal_robustness.py ".\MT5_UTC_EXPORTS\XAUUSD_o_20260904_052959_UTC\XAUUSD_o_M5_bars_utc.csv" --output ".\MT5_UTC_EXPORTS\XAUUSD_o_20260904_052959_UTC\named_session_tpo_temporal_robustness_v1.json"
```

The raw output remains external with the MT5 bundle. A compact result may be committed only after
successful local execution and validation.
