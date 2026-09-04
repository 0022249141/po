# Connectors / Integration Layer

This directory documents how external systems may feed the research repository. **There is no MCP server and no order-execution bridge in this repo.**

See `INTEGRATION_MATRIX.md`.

Principles:

- GitHub is the versioned project source.
- Large/raw source collections may live outside Git and be referenced by provenance.
- ChatGPT consumes curated artifacts and current user-supplied data; it must not redefine project rules.
- MT5/TradingView/Dukascopy/TGJU/macro sources have distinct roles and are not assumed interchangeable.
- No connector implies permission to place or modify trades.
