# Strategy Validation Checklist

## Data
- [ ] dataset manifest exists
- [ ] source/timezone/cutoff known
- [ ] duplicates/order/gaps reviewed
- [ ] forming bars handled explicitly

## Specification
- [ ] specification frozen before final test
- [ ] subjective concepts tagged
- [ ] entry/exit/stop/cancellation exact
- [ ] cost/fill model exact

## Implementation
- [ ] no negative-shift future features
- [ ] no centered rolling in causal signal path
- [ ] no Pine lookahead_on
- [ ] pivots delayed until confirmable
- [ ] no future-index references
- [ ] same-bar fill assumptions documented

## Evaluation
- [ ] trade count reported
- [ ] PF and expectancy reported
- [ ] max DD reported
- [ ] average trade/win/loss reported
- [ ] long/short split reported where applicable
- [ ] IS/OOS defined
- [ ] robustness checks recorded

## Bias control
- [ ] no cherry-picking of only favorable periods
- [ ] parameter search recorded
- [ ] benchmark/baseline preserved
- [ ] rejected runs retained in experiment log
