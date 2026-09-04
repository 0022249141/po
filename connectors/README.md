# Connectors / ChatGPT Integration

The canonical map names three practical integration paths:

1. **Knowledge Files**
2. **GitHub connector**
3. **Google Drive connector**

This repository intentionally contains **no MCP server** after the architecture reset.

## Retrieval strategy

Prefer compact curated artifacts over a raw dump of source PDFs. The canonical map specifically names:

- `glossary.md`
- `SKILL.md`
- `MARKET_PARAMS.md`

These files are expected inputs, not generated placeholders. Their real versions must be recovered before they are used for retrieval.

## GitHub role

GitHub is the version-controlled source for:

- canonical source map
- provenance registry
- normalized knowledge notes
- strategy specifications
- code/backtest artifacts
- validation reports

A connector should retrieve from these versioned artifacts rather than silently altering them.

## Google Drive role

Drive is suitable for the translated PDF collection or other larger user-owned documents when storing all of them directly in Git is undesirable.

## Knowledge-file policy

A curated file should be:

- small enough for reliable retrieval
- terminology-consistent
- source-linked
- explicit about subjective vs operational definitions
- versioned
- free from unsupported confidence/profitability claims

## Boundary

Integration is a transport/retrieval layer. It must not change source definitions, market parameters or Strategy Specification rules.
