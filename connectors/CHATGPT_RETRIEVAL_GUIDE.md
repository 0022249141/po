# ChatGPT Retrieval Guide

This guide defines how an AI session should use the repository. It does not depend on MCP.

## Retrieval order

For project questions:

1. If the user supplied a current file/dataset, read that first.
2. Read the exact frozen Strategy Specification when a strategy is referenced.
3. Read `knowledge/curated/PROJECT_CONTEXT.generated.md`.
4. Read the framework-specific source/index note relevant to the question.
5. Use `config/source-registry.yaml` to identify the allowed external source role.
6. Use external web/source research only when the question requires verification/expansion or project evidence is incomplete.

## Source conflicts

If a current supplied file conflicts with an older curated note, do not silently choose one. State the conflict and prefer the source explicitly selected by the user for that task.

If two frameworks define a similar term differently, preserve both definitions and identify the framework.

## Market-data questions

Before analysis capture:

- symbol
- source
- timeframe(s)
- latest timestamp/cutoff
- timezone
- closed vs forming status
- data-quality warnings

When exact CSV data exists, prefer it to visual estimates from screenshots.

## Strategy questions

Never write or modify a backtest implementation until the Strategy Specification is explicit enough to code without inventing rules. Any discretionary remainder must remain labelled.

## Historical assets

If a user asks about `rtm-fshcd`, `smcp-v3-architecture`, `quant-engine-9phase`, the historic compact `SKILL.md` or other missing artifact, use `config/artifact-registry.yaml` and `docs/MISSING_ASSETS.md`. Do not answer from guessed acronym expansions.

## Recommended compact context pack

Use `knowledge/curated/RAG_PACK_MANIFEST.yaml` as the minimal project pack. Load framework-specific files only when relevant rather than injecting every raw source into every conversation.
