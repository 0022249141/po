# Named Session Policy Protocol — XAUUSD

**Status:** operational context policy  
**Canonical input requirement:** provenance-bound UTC timestamps  
**Implementation:** `research_core/session_policy.py`  
**Policy file:** `config/session-policies/xauusd-major-sessions.yaml`

## Purpose

Define deterministic London, New York and Asia/Tokyo research-session membership on verified UTC data without inferring a broker timezone or flattening daylight-saving transitions into fixed UTC offsets.

This layer is context only. It does not create a trading signal, market bias, ICT kill zone, exchange session, broker maintenance session, or profitability claim.

## Source boundary

The local-clock conventions are derived from broker-education references describing the major FX trading hubs:

- OANDA: `https://www.oanda.com/us-en/skills-and-insights/education/trading-asset-classes/forex/when-is-the-best-time-for-forex-trading/`
- FOREX.com cross-check: `https://www.forex.com/en-us/trading-guides/forex-market-hours/`

The project freezes the following local windows as a **research convention**:

| Session | IANA timezone | Local window |
|---|---|---|
| Asia / Tokyo | `Asia/Tokyo` | 09:00–18:00 |
| London | `Europe/London` | 08:00–17:00 |
| New York | `America/New_York` | 08:00–17:00 |

These windows are not represented as canonical exchange hours or as methodology-specific kill zones.

## Membership semantics

- Input timestamp must be timezone-aware and is normalized to UTC.
- Membership is evaluated from the bar-open timestamp for bar-based research.
- Start is inclusive; end is exclusive.
- Monday through Friday is evaluated in each session's own local timezone.
- Overlap is allowed and preserved; an instant may belong to more than one session.
- Session instance id is `<session_id>:<local-calendar-date>`.
- Cross-midnight windows are supported by the engine even though the current three windows do not cross midnight.

## DST rule

No fixed UTC offsets are stored for London or New York. Python `zoneinfo` resolves IANA timezone rules for the requested date.

This intentionally preserves periods when US and UK DST transitions do not occur on the same date. For example, during the March transition gap New York may have shifted to daylight time while London is still on GMT. The policy must not force a constant London–New York UTC relationship.

`tzdata` is a project dependency so the same IANA database interface is available on Windows systems that do not provide a system timezone database.

## Data-quality rule

Session boundaries are independent of whether the broker feed actually contains every expected bar.

- Missing bars do not move or shrink the session window.
- A holiday or maintenance break is not inferred from absence alone.
- Downstream dataset adapters must mark incomplete session instances when expected bars are absent.
- A partial current session at dataset cutoff is a coverage edge, not automatically a data defect.

## Canonical XAUUSD eligibility

The named-session layer is authorized only for the new canonical UTC dataset whose timebase registry status is `verified`:

`xauusd_o_utc_20260904_052959`

The older source-local bundle remains ineligible for authoritative named-session mapping.

## Validation gates

The policy is accepted only if:

1. all timezones are valid IANA identifiers;
2. local windows parse deterministically;
3. weekday lists are valid;
4. fixed UTC offsets remain prohibited;
5. tests demonstrate winter/summer DST changes;
6. tests preserve the US/UK DST mismatch period;
7. start-inclusive/end-exclusive behavior is deterministic;
8. overlap classification is deterministic;
9. repository lookahead audit remains clean.

## Explicit non-equivalence

`Asia/Tokyo`, `London`, and `New York` in this policy are major-hub research sessions. They must not be silently substituted for:

- ICT London Kill Zone;
- ICT New York Kill Zone;
- London Close Kill Zone;
- Asia range definitions from another methodology;
- exchange-specific regular trading hours;
- broker rollover/maintenance windows.

Any such concept requires its own source-backed policy and tests.
