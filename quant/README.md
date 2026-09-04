# Quant / Backtesting Layer

This layer exists to convert source-derived concepts into reproducible tests. It does not define concepts by itself.

## Required workflow

1. **Strategy Specification freeze**
2. dataset/provenance validation
3. baseline implementation
4. lookahead/repaint/future-leakage audit
5. execution-model audit
6. transaction-cost model
7. in-sample run
8. out-of-sample run
9. robustness/sensitivity tests
10. result registry

## Required metrics

At minimum:

- trade count
- net profit
- Profit Factor
- expectancy
- maximum drawdown
- average win / average loss
- average trade
- long vs short performance
- consecutive losses
- equity stability
- transaction costs
- IS vs OOS behavior
- robustness across periods/assets when appropriate

## Named dependency from the canonical map

`quant-engine-9phase` is referenced by name in the source map, but its actual implementation is not currently present in this repository. It remains a Missing Asset and must not be reconstructed from the name alone.

## Implementation reference sources

- MetaTrader5 Python package — optional bridge/reference for data work.
- MQL5 Articles — implementation/reference archive.
- GitHub SMC/ICT repositories — code cross-check only.

## Bias controls

Every test must explicitly check:

- lookahead bias
- repainting
- future leakage
- pivot confirmation timing
- unrealistic fills
- commission/spread/slippage
- sample size
- overfitting
- cherry-picking
- regime dependency
