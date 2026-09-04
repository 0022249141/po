# Auction Market Theory / Market Profile — Verified Source Note

## Provenance

- framework: `auction_market_theory`
- concept_id: `amt_market_profile_core`
- concept_name: `Market Profile / auction-process core`
- source_ids:
  - `cme_market_profile_education`
  - `dalton_mind_over_markets`
  - `dalton_markets_in_profile`
- source_class: `exchange_education + publisher_book_metadata`
- ingestion_state: `source_noted`
- verified_date: `2026-09-04`

## Exact source locators

- CME Group glossary: `https://www.cmegroup.com/education/glossary`
- Wiley Online Books — *Mind Over Markets*: `https://onlinelibrary.wiley.com/doi/book/10.1002/9781118659724`
- Wiley Online Books — *Markets in Profile*: `https://onlinelibrary.wiley.com/doi/book/10.1002/9781119196709`

## Source-faithful statements

### CME Group

CME defines Market Profile as an analytical tool that organizes **price and time** information to reveal developing trends/patterns and to identify areas where price is being accepted or rejected.

### Dalton — *Mind Over Markets*

Wiley describes the updated edition as a Market Profile method focused on market-generated information. The publisher summary explicitly references market structure, value areas, price rejection points, and assessment of buyer/seller strength.

### Dalton — *Markets in Profile*

Wiley describes Market Profile as a multidimensional representation of the market's continuing auction process. The book combines Market Profile, behavioral finance, and neuroeconomics to interpret market dynamics and decision-making.

## What is verified at this stage

The sources support the following native-framework ideas:

1. Market Profile is an **auction-process / market-generated-information** framework.
2. Price acceptance and price rejection are native Market Profile concepts.
3. Value areas are explicitly part of the Dalton Market Profile material.
4. Market structure is interpreted through the evolving auction rather than by importing ICT/RTM terminology.

## What is NOT yet verified as an operational rule

This note does **not** establish a canonical machine formula for:

- Value Area percentage or expansion algorithm;
- POC calculation method;
- TPO letter construction/session segmentation;
- initiative vs responsive trigger thresholds;
- entry/exit rules;
- any XAUUSD-specific session template.

Those items remain `defined`/`operational_candidate` work only after an exact source passage, chapter/page, or official specification is captured.

## Data boundary

CME's definition is based on price/time organization. Any later Volume Profile, volume-at-price, or POC implementation must declare its actual input data. Broker tick volume cannot be relabelled as centralized exchange volume.

## Cross-framework boundary

Do not translate Market Profile acceptance/rejection, Value Area, or auction balance directly into ICT dealing ranges, RTM structures, or dealer inventory variables. Any such mapping requires a separate crosswalk after both source-side definitions are independently established.

## Ambiguities / unresolved items

- Exact canonical POC and Value Area algorithms for this project are not yet source-captured.
- Dalton books are verified bibliographically/publisher-summary level here; chapter/page-level extraction is still pending.
- `initiative activity` and `responsive activity` are named project concepts but are not promoted by this note alone.
