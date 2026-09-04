# XAUUSD Timebase Candidate Evidence — 2026-07-22

## Evidence class

`terminal_observation`

## Observation

A prior user-provided read-only MT5 terminal observation recorded the following clocks at the same sampling event:

- trusted UTC clock: `2026-07-22T07:56:19Z`
- local Asia/Tehran clock: `2026-07-22T11:26:19` (UTC+03:30)
- MT5 trade-server last-known clock: `2026-07-22T10:56:18`

The same observation identified the connected terminal as:

- company: `LiteFinance Global LLC`
- server: `LiteFinance-MT5-Live`
- terminal: LiteFinance MetaTrader 5

The observed trade-server clock is therefore consistent with approximately **UTC+03:00** at that observation instant.

## Binding limitation

This observation was associated with a previous LiteFinance terminal context and `XAUUSD_l` availability. The currently qualified research bundle uses symbol `XAUUSD_o` and its export metadata does not independently bind those files to the same broker/server instance.

Therefore this evidence supports only a **candidate mapping** for the current bundle. It does not prove that `XAUUSD_o` timestamps on 2026-09-03 use UTC+03:00, and it does not establish the server's DST history.

## Consequence

- candidate source offset: `UTC+03:00`
- named-session use: **not authorized**
- UTC/Tehran conversion for the current `XAUUSD_o` bundle: **not yet authoritative**
- required next evidence: terminal/export metadata tied directly to the exact current bundle, plus DST policy/history

The original terminal transcript is not committed to the repository because it contains unrelated account/session information. Only the minimum non-sensitive timebase observation is preserved here.
