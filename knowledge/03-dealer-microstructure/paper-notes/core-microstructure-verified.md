# Core market-microstructure references — verified notes

## Provenance

Evidence captured: 2026-09-04 from publisher/academic index pages for the four canonical references.

## Kyle (1985) — `kyle_1985`

**Continuous Auctions and Insider Trading**, Econometrica 53(6), 1315–1336.

Verified model roles:
- one risk-neutral informed insider;
- random/noise traders;
- competitive risk-neutral market makers;
- private information is progressively incorporated into prices;
- market depth/liquidity and informational price impact are explicit model objects.

Evidence boundary: this paper supports theory about informed trading, price impact and market depth. It does not reveal a live dealer's inventory or hidden orders.

## Glosten–Milgrom (1985) — `glosten_milgrom_1985`

**Bid, ask and transaction prices in a specialist market with heterogeneously informed traders**, Journal of Financial Economics 14(1), 71–100.

Verified model role:
- adverse selection from heterogeneously informed traders can generate a positive bid–ask spread even for a risk-neutral specialist with zero expected profit;
- transaction prices convey information.

Evidence boundary: this supports adverse-selection/spread theory, not direct inference of current informed order flow from price alone.

## Ho & Stoll (1981) — `ho_stoll_1981`

**Optimal dealer pricing under transactions and return uncertainty**, Journal of Financial Economics 9(1), 47–73.

Verified model role:
- dealer bid/ask decisions depend on the dealer's state, including inventory, return variance and stochastic transaction arrivals;
- inventory risk is an explicit determinant of optimal dealer pricing.

Evidence boundary: the model explains how inventory can influence quotes in theory. It does not provide visibility into the live inventory of a bank/dealer.

## Grossman–Miller (1988) — `grossman_miller_1988`

**Liquidity and Market Structure**, Journal of Finance 43(3), 617–633.

Verified model role:
- liquidity is modeled through demand and supply of immediacy;
- market makers supply immediacy by continuous presence and willingness to bear risk while final counterparties are absent;
- equilibrium liquidity depends on this risk-bearing capacity.

Evidence boundary: this supports an immediacy/liquidity-provision interpretation, not claims that a specific observed candle proves dealer inventory or bank positioning.

## Project usage

These references may support theory labels such as:

- `informed_trading`
- `adverse_selection`
- `inventory_risk`
- `liquidity_provision`
- `immediacy`
- `price_impact`

They may **not** be converted directly into an execution signal or confluence score without an explicit measurable proxy, frozen rule, and separate backtest.

## Promotion state

`source_verified_partial`
