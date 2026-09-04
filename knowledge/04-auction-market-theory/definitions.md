# Auction Market Theory / Market Profile — Source-grounded definitions

Only concepts directly supported by the currently verified CME/Dalton source note are promoted here.

## `amt_market_profile_core`

- source_ids: `cme_market_profile_education`, `dalton_mind_over_markets`, `dalton_markets_in_profile`
- state: `defined`

Market Profile is treated in this project as an auction-process / market-generated-information framework that organizes price and time to expose developing structure and areas of acceptance or rejection.

This is a conceptual definition, not a complete TPO or Volume Profile implementation specification.

## `amt_price_acceptance_rejection`

- source_id: `cme_market_profile_education`
- state: `defined`

Price acceptance/rejection refers to the Market Profile interpretation of areas where the auction spends/organizes time versus areas that are not similarly accepted. The current verified source supports the concept but does not provide a machine threshold for classifying acceptance or rejection.

Therefore this concept remains `defined`, not `operational`.

## Concepts intentionally not yet promoted to `defined`

### `amt_value_area`

The Dalton material explicitly references value areas, but the current source capture does not establish the project's canonical percentage, expansion procedure, tie handling, or session construction. State remains `source_noted`.

### `amt_poc`

A canonical project POC calculation has not yet been source-captured. State remains `source_indexed`.

### `amt_initiative_activity` / `amt_responsive_activity`

These are named project concepts, but no exact verified source passage defining trigger criteria is captured yet. State remains `source_indexed`.

## Data boundary

Any later volume-at-price implementation must name the actual data source and aggregation method. Broker tick volume may be used only when explicitly labelled as broker tick volume; it must not be represented as centralized exchange volume.
