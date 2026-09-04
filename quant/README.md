# Quant Research Layer

The quant layer turns a **source-backed or explicitly generated hypothesis** into a reproducible test. It does not treat visual confluence as statistical evidence.

## Workflow

`question → operational rule → frozen spec → implementation → lookahead audit → baseline → IS/OOS → robustness → scoped verdict`

Templates are in `quant/templates/`.

## Tools

- `tools/summarize_backtest.py` — trade-level P&L summary
- `tools/audit_lookahead.py` — static warning scan
- `tools/quality_check.py` — repository-level gate

## Required metrics

Trade count, Net Profit, Profit Factor, Expectancy, Max Drawdown, Average Win/Loss, Average Trade, Long/Short split, Consecutive Losses, cost assumptions, IS/OOS and robustness.

Win rate alone is not an edge metric.
