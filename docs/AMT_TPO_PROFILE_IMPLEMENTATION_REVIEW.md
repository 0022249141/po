# AMT TPO Profile — Implementation Review

**Operational rule:** `amt_tpo_profile_core_v1`  
**Candidate:** `quant/candidates/AMT_TPO_PROFILE_CORE.yaml`  
**Implementation:** `research_core/tpo_profile.py`  
**Tests:** `tests/test_tpo_profile.py`

## Verdict

`PASS — promote descriptive TPO occupancy engine from operational_candidate to operational.`

This verdict applies only to the deterministic descriptive engine. It does not promote POC, Value Area, initiative/responsive activity, trading entries, exits, or profitability claims.

## Candidate-to-code audit

- closed-bar event clock: implemented;
- forming bars: strict no-op;
- same forming timestamp may later be processed once as closed;
- session reset: implemented on externally supplied `session_id` change;
- timezone/DST inference: absent;
- integer-grid occupancy: implemented with Decimal arithmetic;
- normalization rule: `ROUND_HALF_UP(price / price_increment)` and frozen in the operational rule artifact;
- inclusive normalized `[low_tick, high_tick]` occupancy: implemented;
- strictly increasing closed timestamps: enforced;
- duplicate closed timestamp: rejected;
- non-positive increment: rejected;
- empty session id: rejected;
- externally detected source gap: retained profile is marked incomplete;
- POC / Value Area / signal logic: absent by design.

## Deterministic test coverage

1. inclusive closed-bar bin population;
2. forming-bar no-op followed by close at same timestamp;
3. reset on session change;
4. duplicate/out-of-order closed timestamp rejection;
5. incomplete-profile marking when an upstream gap is supplied.

## Lookahead boundary

The engine is incremental and reads only the arriving bar plus current state. No centered window, negative shift, future pivot, later-session extreme, or retrospective session label is used inside the engine.

Repository CI still runs the static lookahead audit independently.

## Dataset-application boundary

The engine is generic and operational, but a named XAUUSD session application remains conditional on explicit session provenance. The existing qualified XAUUSD bundle still has unresolved source/server timezone and DST metadata, so this promotion does not authorize London/NY/Asia session claims on that bundle.

## Source boundary

Market Profile source material supports organizing price/time and interpreting auction structure. The exact integer-grid occupancy, rounding, and state-management rules here are labelled project operational choices, not canonical Dalton/CME formulas.
