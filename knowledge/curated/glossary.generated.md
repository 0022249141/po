# Curated Glossary — Generated Baseline

> **Generated artifact.** This is not the recovered historical `glossary.md` referenced by the canonical map. It provides a safe operational vocabulary for new work while preserving framework-specific definitions.

## Evidence / research vocabulary

| Term | Operational meaning in this repository |
|---|---|
| Observed Data | Value directly present in a supplied dataset/file/chart or measured by reproducible code. |
| Source Definition | Definition attributable to a named source/framework. |
| Interpretation | Analytical mapping of observed/source evidence. Not a fact. |
| Hypothesis | Testable proposition not yet statistically validated. |
| Backtested Evidence | Reproducible output from a frozen specification, known dataset and execution model. |
| Cutoff | Latest timestamp permitted for an analysis. Data after cutoff is forbidden. |
| Forming Candle | Candle whose interval is not complete at cutoff; cannot be silently treated as closed. |
| Provenance | Source, retrieval/version metadata, processing steps and checksum linking an artifact to origin. |
| IS | In-Sample period used for development/estimation. |
| OOS | Out-of-Sample period reserved for evaluation. |
| Lookahead Bias | Using information not available at the simulated decision time. |
| Repainting | Historical signal/plot state changing as later data arrives or as confirmation occurs. |
| Future Leakage | Any path by which future observations influence earlier features/signals/labels. |

## Cross-framework market vocabulary

These are **project-level descriptors**, not claims that every framework uses identical definitions.

| Term | Project treatment |
|---|---|
| Swing High / Swing Low | Requires a strategy-specific objective pivot rule before backtesting. Visual-only use is `DISCRETIONARY`. |
| BOS | Structure-break label. Exact reference swing, close/wick rule and minimum displacement must be defined per specification. |
| CHoCH | Potential change-of-character label. Definition varies across communities; exact rule must be source/spec specific. |
| MSS | Market Structure Shift. Not assumed equivalent to CHoCH; operational rule must be stated. |
| Liquidity Pool | A hypothesized concentration/objective associated with prior highs/lows/equal levels. It is not proof of orders. |
| Liquidity Sweep | Price trading beyond a defined liquidity reference and satisfying an explicit reclaim/close rule if the strategy requires one. Sweep alone is not confirmed reversal. |
| Displacement | Large directional repricing; objective threshold must be specified (range, body, ATR, etc.) before testing. |
| FVG | Three-candle imbalance concept in ICT/SMC usage; exact wick/body and mitigation rules are specification-dependent. |
| Order Block | Source/framework-dependent concept. No universal project definition is assumed. |
| Premium / Discount | Position within a defined dealing range; range construction must be explicit. |
| Inducement | Interpretive liquidity concept unless operationalized. Default status: `DISCRETIONARY`. |

## RTM vocabulary — source-specific status

The canonical map names these terms as RTM/Markepedia vocabulary. Definitions must be ingested from ReadTheMarket/RTM Academy before being treated as canonical:

- FTR — pending official-source definition
- BSZ — pending official-source definition
- MPL — pending official-source definition
- Quasimodo — pending official-source definition
- Compression — pending official-source definition

Do not substitute generic SMC definitions.

## Auction / Market Profile vocabulary

| Term | Project treatment |
|---|---|
| POC | Point of Control; exact calculation depends on the profile implementation/data basis. |
| Value Area | Price region containing a configured share of profile activity; method and percentage must be specified. |
| Initiative Activity | Auction behavior framed as participants driving price away from accepted value; source-specific details belong in AMT notes. |
| Responsive Activity | Auction behavior framed as response back toward accepted value; source-specific details belong in AMT notes. |

## Academic microstructure vocabulary

| Term | Project treatment |
|---|---|
| Inventory Risk | Risk borne by a dealer/market maker from holding inventory while prices move. |
| Adverse Selection | Loss/risk from trading against better-informed counterparties. |
| Immediacy | Ability to execute without waiting; liquidity suppliers may bear risk to provide it. |
| Market Depth | Sensitivity/available liquidity around prices; exact model definition depends on source. |
| Informed Trader | Model-specific participant with private information; not a claim about identifiable live-market actors. |

## Naming conventions

- source ids: `snake_case`
- dataset ids: `<market>_<source>_<datatype>_<YYYYMMDD-or-range>`
- strategy specs: `SPEC-<slug>-vMAJOR.MINOR`
- backtest runs: `RUN-<spec-id>-<dataset-id>-<timestamp>`
- generated documents: suffix `.generated.md`
- original/recovered documents: preserve original filename and record provenance separately
