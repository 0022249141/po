# Implementation Plan

## Phase 0 — Canonicalize repository

**Goal:** make the Resource Connector Map the source of truth.

Completed:
- remove MCP server and MT5 bridge from this repository
- remove MCP-specific Node package configuration
- add canonical map under `docs/`
- define repository architecture and source policy
- create source registry and pipeline manifest

Acceptance criterion: repository can be understood without any MCP/runtime code.

## Phase 1 — Recover existing assets

Bring the real versions of the assets already referenced by the map into the repository or link them by exact location:

- glossary.md
- SKILL.md
- MARKET_PARAMS.md
- rtm-fshcd
- smcp-v3-architecture
- quant-engine-9phase
- BTMM / MMXM / ICT London Close Killzone / Choch Plan / 1AM CRT translation artifacts
- translated PDF collection
- general-platforms CSV specification/sample

Acceptance criterion: every item in `MISSING_ASSETS.md` is either present, linked to an exact external location, or explicitly marked unavailable.

## Phase 2 — Build source registry and provenance

For each source in the canonical map:

1. assign stable `source_id`
2. record canonical location
3. classify as official / academic / data / implementation
4. record ingestion permission and storage policy
5. add retrieval/version metadata
6. record what role the source is allowed to play

Acceptance criterion: no knowledge note exists without a `source_id`.

## Phase 3 — Knowledge ingestion by framework

Process frameworks independently:

### 3.1 ICT / SMC / Wyckoff
- official ICT material
- Wyckoff Analytics material
- definitions and vocabulary
- source notes
- operational rules only when objectively definable

### 3.2 RTM
- ReadTheMarket
- RTM Academy
- Markepedia vocabulary: FTR / BSZ / MPL / Quasimodo / Compression
- no third-party PDF repost as authority

### 3.3 Dealer / Market Microstructure
- bibliographic records for the four classic papers
- source notes for inventory risk / informed trading
- notes for the two specified arXiv papers
- explicit boundary: theory is not direct dealer-order visibility

### 3.4 Auction Market Theory
- Dalton books as bibliographic sources
- CME education material
- Value Area / POC / Initiative / Responsive vocabulary

Acceptance criterion: each framework has source notes, glossary entries and an explicit list of subjective vs operationalizable concepts.

## Phase 4 — Data layer

### Iran Gold
- define general-platforms CSV schema from a real sample
- define TGJU cross-check procedure
- record timestamps/timezone/data quality

### XAUUSD
- define Dukascopy historical dataset procedure
- define MT5 import format from user-provided exports
- define TradingView visual cross-check role
- define macro-event table from TradingEconomics/ForexFactory

Acceptance criterion: a dataset cannot enter backtesting without provenance and schema validation.

## Phase 5 — Quantification

For every concept selected for testing:

1. freeze Strategy Specification
2. define state variables
3. define swing/pivot rules
4. define entry and exit rules
5. define transaction costs
6. implement baseline
7. audit lookahead/repainting/future leakage
8. run IS/OOS
9. record PF, expectancy, drawdown, trade count, average trade, long/short split and robustness

Acceptance criterion: no result labelled `validated` without reproducible output and specification version.

## Phase 6 — Curated RAG files

Create compact retrieval artifacts only after source normalization:

- glossary
- framework skill/rule documents
- market parameters
- cross-framework crosswalks
- data schema notes
- validated strategy specifications

Raw source dumps are not used as the primary retrieval layer.

Acceptance criterion: every curated statement links back to source/provenance or backtest evidence.

## Phase 7 — ChatGPT integration

Use GitHub/Drive/Knowledge Files according to the canonical map. The integration layer consumes curated artifacts; it does not redefine them.

Acceptance criterion: a fresh ChatGPT session can retrieve the project vocabulary, source policy, market parameters and validated specifications without relying on hidden context.
