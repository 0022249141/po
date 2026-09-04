# Knowledge Protocol

## Evidence classes

Every curated statement must be identifiable as one of:

1. **Source Definition** — what a named source/framework explicitly defines.
2. **Observed Data** — directly measured from a dataset/chart/file.
3. **Interpretation** — analyst mapping of evidence to a framework.
4. **Hypothesis** — a testable proposition not yet validated.
5. **Backtested Evidence** — output from a reproducible frozen specification.

Do not collapse these classes.

## Framework isolation

### ICT / SMC / Wyckoff
Store source-specific vocabulary and rules without claiming all SMC terms are universal or identical to ICT/Wyckoff definitions.

### RTM
Use ReadTheMarket/RTM Academy material for RTM vocabulary. Do not redefine FTR/BSZ/MPL/Quasimodo/Compression from generic SMC analogies.

### Dealer / Market Microstructure
Academic models explain mechanisms such as inventory risk, adverse selection and immediacy. They do not provide direct evidence of a broker/dealer's live inventory, hidden orders, DOM, CVD or institutional intent unless such data is actually supplied.

### Auction Market Theory
Keep Market Profile/Auction concepts in their own vocabulary. Crosswalks may map concepts for comparison but must not declare equivalence without evidence.

## Curated retrieval artifact rules

- Compact normalized notes are preferred over raw dumps.
- Every source-derived note includes `source_id`.
- Generated synthesis is labelled generated.
- Historical artifacts are never reconstructed under their original filenames unless recovered exactly.
- Conflicting source definitions are preserved as conflicts, not silently reconciled.
- Subjective concepts are tagged `DISCRETIONARY` until an operational rule is specified.

## Recommended note header

```yaml
note_id: ...
framework: ...
source_ids: [...]
evidence_class: source_definition|observed|interpretation|hypothesis|backtested
status: draft|reviewed|validated|deprecated
generated: true|false
reviewed_at: YYYY-MM-DD
```
