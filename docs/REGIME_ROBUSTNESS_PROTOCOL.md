# Regime Robustness Protocol

## Scope

`XAUUSD_NAMED_SESSION_TPO_REGIME_ROBUSTNESS_V1` is a declared post-result robustness follow-up.
It does **not** redefine the prior aggregate or temporal studies and does not introduce a trading
signal. The only new element is a causal, project-defined conditioning label.

## Why the regime definition is lagged

Using the current London/New York range to label that same date and then comparing current-session
range by the label would be circular. V1 therefore prohibits any current-date outcome from
participating in its own regime label.

For paired complete London/New York dates, define:

`composite_range[D] = (London range_ticks[D] + NewYork range_ticks[D]) / 2`

For current paired date `D`, take the immediately preceding 20 **paired complete dates** only.
The most recent prior date's composite range is ranked within those 20 prior values using:

`midrank = (count_less + 0.5 * count_equal) / n`

The current date receives:

- `low` when midrank `< 1/3`
- `normal` when `1/3 <= midrank < 2/3`
- `high` when midrank `>= 2/3`

Thus the label for date `D` is fully knowable before either current-date research session is used
in the study outcome.

## Pairing and sample policy

- Primary sessions: London and New York only.
- Input: canonical verified-UTC M5 dataset.
- Selection: `complete_only`; coverage edges excluded.
- A paired date exists only when both primary sessions have a complete selected instance for the
  same session-local start date.
- First 20 paired dates are warm-up only and receive no regime label.
- A regime is eligible only when both primary sessions have at least 10 labeled dates in it.

## Outcome features

Directional persistence is evaluated only for:

- `range_ticks`
- `occupancy_events`

The following remain descriptive context:

- `occupied_bins`
- `mean_bin_occupancy`
- `bars_seen`

## Governance boundary

This is a **project-defined causal lagged-range conditioning rule**, not a canonical volatility
regime, macro regime, ICT concept, AMT regime, or dealer-inventory state.

No statistical-significance test is performed in V1. No threshold may be tuned after seeing the
regime result; any change requires a new frozen version.

## Execution

```powershell
py tools\validate_regime_robustness.py

py tools\run_named_session_tpo_regime_robustness.py `
  ".\MT5_UTC_EXPORTS\XAUUSD_o_20260904_052959_UTC\XAUUSD_o_M5_bars_utc.csv" `
  --output ".\MT5_UTC_EXPORTS\XAUUSD_o_20260904_052959_UTC\named_session_tpo_regime_robustness_v1.json"
```

The raw JSON remains outside Git until reviewed. A compact result record is created only after a
successful user-local execution is inspected.
