# Asset Definition Audit

## Scope

This document audits the supplied descriptions of assets named by `docs/resource-connector-map.md`.

**Important:** a description, inferred expansion, or generic convention is not the same thing as recovering the original project artifact. No item below is considered recovered unless the real file, repository path, commit, source document, or exact content is available.

Status vocabulary:

- `role_supported` — the supplied text is useful only for describing the likely role of an artifact.
- `externally_verified_term` — the public meaning of the term was independently verified, but the project's original artifact is still missing.
- `unsupported_inference` — the proposed expansion/content is not supported by the canonical map or available project evidence.
- `project_mismatch` — the supplied description belongs to another domain and must not be imported into this trading repository.
- `missing_original` — original artifact/content is still absent.

---

## 1. `glossary.md`

**Audit:** `role_supported` + `missing_original`

The supplied description (terminology, abbreviations, naming conventions, project vocabulary) is a reasonable generic role for a glossary. However, it does not recover the project's actual `glossary.md`.

**Repository action:** do not fabricate the file. When the real glossary is recovered, preserve source-specific definitions and distinguish objective definitions from discretionary trading language.

---

## 2. `SKILL.md`

**Audit:** `role_supported` + `missing_original`

The supplied description is a generic interpretation of a skill/capability document. The canonical map specifically refers to an existing compact `SKILL.md` described as a current "6-layer + verdict" version. Therefore a newly invented strategies/API/capabilities document would not be equivalent to the referenced artifact.

**Repository action:** keep missing until the referenced real version is recovered.

---

## 3. `MARKET_PARAMS.md`

**Audit:** `project_mismatch` + `missing_original`

The supplied `loanToken`, `collateralToken`, `oracle`, `irm`, and `lltv` fields are DeFi lending-market parameters. Nothing in the canonical map indicates that this trading project uses a Morpho Blue/DeFi market-parameter schema.

For this repository, `MARKET_PARAMS.md` is expected to be a trading-market configuration artifact only if/when the original file is recovered (e.g. symbol/session/timezone/tick/contract/data rules), but its exact schema must not be guessed.

**Repository action:** reject the DeFi definition for this project.

---

## 4. `rtm-fshcd`

**Audit:** `unsupported_inference` + `missing_original`

The expansion "Read The Market - Full Systematic Hybrid Core Data" is speculative. The canonical map only establishes that `rtm-fshcd` is an internal skill/system name associated with RTM formalization; it does not define the acronym.

**Repository action:** retain exact identifier `rtm-fshcd`; do not expand or redefine it until the original asset is found.

---

## 5. `smcp-v3-architecture`

**Audit:** `unsupported_inference` + `missing_original`

The supplied interpretation as "Secure Model Context Protocol v3" (wire protocol, key schedule, A2A security, policy enforcement) is not supported by the canonical map or current repository evidence.

Given this repository's trading context, importing a separate security-protocol architecture under this name would risk severe knowledge contamination.

**Repository action:** keep the identifier opaque until its actual file/repository/commit is recovered. Do not treat it as MCP/SMCP security infrastructure.

---

## 6. `quant-engine-9phase`

**Audit:** `role_supported` at a generic level + `unsupported_inference` for exact phases + `missing_original`

The proposed nine-stage quant workflow (ingestion, features, research, training, backtest, validation, portfolio optimization, execution, risk) is a plausible generic quantitative-research lifecycle, but there is no evidence that these are the exact nine phases of the referenced internal engine.

The canonical map only indicates that the project previously had an internal `quant-engine-9phase` and that MQL5 articles were a source for it.

**Repository action:** preserve the generic lifecycle as an external design reference only; do not label it as the original engine specification.

---

## 7. BTMM

**Audit:** `externally_verified_term` + `missing_original_translation_asset`

The proposed expansion "Breaker Trader Market Maker" is incorrect for the source family referenced by the map. Public primary/near-primary material identifies BTMM as **Beat the Market Maker**, associated with Steve Mauro.

Verification:
- https://www.beatthemarketmaker.com/
- Steve Mauro / Beat the Market Maker public course material

The canonical map says BTMM was already covered by the user's existing PDF translation pipeline. Therefore the real translated artifact remains required.

**Repository action:** canonical public label = `Beat the Market Maker (BTMM)`; original translated project asset remains missing.

---

## 8. MMXM

**Audit:** `externally_verified_term` + `missing_original_translation_asset`

The supplied expansions "Market Maker X-Ray Method" / "Market Microstructure X-Model" are not supported. In ICT-related material, MMXM refers to the **Market Maker Model**, including Market Maker Buy Model (MMBM) and Market Maker Sell Model (MMSM) terminology.

Verification references:
- public ICT-related Market Maker Buy/Sell Model material
- https://www.theinnercircletraders.com/ict-trading-mmxm-macros-model/

This verification establishes the public term, not the contents of the user's translated MMXM artifact.

**Repository action:** use `Market Maker Model (MMXM)` as the public label; keep project translation asset missing until recovered.

---

## 9. ICT London Close Killzone

**Audit:** `externally_verified_term` with timing correction + `missing_original_translation_asset`

The supplied 15:00–17:00 **EST** statement mixes local New York time with UTC. ICT's own London Close lesson exists publicly, and commonly documented ICT timing is approximately **10:00 AM–12:00 PM New York time**. That corresponds to 15:00–17:00 UTC during EST and 14:00–16:00 UTC during EDT.

Primary public lesson:
- https://www.youtube.com/watch?v=3OEUIkkcmLE

**Repository action:** store session rules in New York wall-clock time with explicit DST conversion; do not hard-code "15:00–17:00 EST".

---

## 10. Choch Plan

**Audit:** `role_supported` + `missing_original_translation_asset`

The supplied description of CHoCH as a potential change in structure is generic trading knowledge. It does not establish the exact rules, trigger, timeframe, entry, invalidation, or exit logic of the referenced `Choch Plan` asset.

**Repository action:** no Strategy Specification may be reconstructed from this description. Recover the original translated plan first.

---

## 11. 1AM CRT

**Audit:** `externally_supported_term_family` + `unsupported_inference` for supplied expansion/time rationale + `missing_original_translation_asset`

The supplied expansion "1 AM Central Time" / "Critical Reversal Time" is not sufficiently supported. In current trading usage, CRT commonly refers to **Candle Range Theory**, and public material explicitly uses the phrase "1AM Candle Range Theory".

The exact timezone, anchor candle, market, and rules of the user's referenced `1AM CRT` document must come from that original asset rather than inference.

**Repository action:** do not encode Central Time, Asia-open rationale, or a reversal rule until the original document is recovered.

---

## 12. `44 translated PDFs`

**Audit:** `role_supported` + `missing_originals`

The supplied description only identifies them generically as translated trading documents. It does not identify titles, hashes, versions, source URLs, translation dates, or provenance.

**Repository action:** when recovered, create an inventory with at least:

- stable document id
- filename/title
- framework/category
- original source/author
- original language
- translation language
- translation/version date
- checksum/hash
- processing status
- copyright/storage policy
- derived curated-note links

Do not use raw PDF dumps as the primary RAG layer.

---

## 13. `general-platforms` CSV specification

**Audit:** `unsupported_inference` + `missing_original_sample/spec`

The supplied trade-history schema (`Symbol`, `Side`, `Entry Price`, `Exit Price`, P&L, etc.) is not supported by the canonical map. The map describes `general-platforms` CSV as the user's existing **intraday data feed format**, not necessarily a trade-history interchange format.

**Repository action:** the schema must be inferred only from a real sample file. Required validation will include timestamp, timezone, symbol, OHLC/tick fields as applicable, missing rows, duplicates, ordering, and forming-vs-closed candle handling.

---

## 14. `rolling(center=True)` fix

**Audit:** supplied explanation rejected; likely implementation/lookahead issue; original commit still missing.

The supplied explanation treats this as an old pandas bug fixed to reduce lag. That is not supported by the canonical map.

In time-series trading code, `rolling(..., center=True)` intentionally centers a window around the current observation. For signal generation/backtesting this can consume future observations and therefore create **future leakage / lookahead bias** unless used only for retrospective labeling/visualization with explicit safeguards.

The canonical map's wording about a recent `rolling(center=True)` fix is therefore treated as an internal implementation correction until the exact code/commit is recovered.

**Repository action:** any recovered implementation must be audited for future leakage before its results are accepted.

---

# Final classification

## Can be used now as terminology/role context

- generic intended role of `glossary.md`
- generic intended role of `SKILL.md`
- generic quant lifecycle as a non-canonical design reference
- BTMM public label = Beat the Market Maker
- MMXM public label = Market Maker Model
- ICT London Close public session concept (with corrected timezone handling)
- CHoCH generic concept only
- CRT term family likely Candle Range Theory, pending original `1AM CRT` asset

## Must NOT be imported as project truth

- DeFi `MARKET_PARAMS.md` schema
- guessed expansion of `rtm-fshcd`
- Secure Model Context Protocol interpretation of `smcp-v3-architecture`
- guessed exact nine phases of `quant-engine-9phase`
- Breaker Trader Market Maker expansion of BTMM
- Market Maker X-Ray / Market Microstructure X-Model expansion of MMXM
- 15:00–17:00 EST London Close timing
- Central Time / Critical Reversal Time expansion of 1AM CRT
- trade-history interpretation of `general-platforms` CSV
- pandas-library-bug interpretation of `rolling(center=True)`

## Recovery rule

No item moves from `missing` to `recovered` until the repository has an exact original file, source path, commit, or user-provided canonical content with provenance.