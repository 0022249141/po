# Dealer / Market Microstructure — Source-grounded definitions

These definitions are theory labels supported by the verified academic references. They are not live-market state estimators and they do not reveal hidden dealer inventory or orders.

## `dealer_informed_trading`

- source_id: `kyle_1985`
- state: `defined`

Trading in which an agent possesses private information and trades while that information is progressively incorporated into prices through market interaction.

Project boundary: this concept does not imply that informed trading can be identified from one candle or one price pattern without a measurable proxy.

## `dealer_adverse_selection`

- source_id: `glosten_milgrom_1985`
- state: `defined`

The risk to a liquidity supplier that a counterparty may possess superior information. In the cited model, this information asymmetry can generate a positive bid–ask spread even for a risk-neutral specialist with zero expected profit.

Project boundary: observed spread alone does not identify who is informed.

## `dealer_inventory_risk`

- source_id: `ho_stoll_1981`
- state: `defined`

Risk arising from the dealer's inventory state and uncertainty about returns and future transaction arrivals; in the cited model, inventory is an explicit determinant of optimal bid/ask pricing.

Project boundary: this is a theoretical state variable. The project has no direct observation of a live bank/dealer inventory unless an actual data source provides it.

## `dealer_liquidity_provision`

- source_id: `grossman_miller_1988`
- state: `defined`

The supply of trading immediacy by market makers who remain present and accept risk while final counterparties are not immediately available.

## `dealer_immediacy`

- source_id: `grossman_miller_1988`
- state: `defined`

The ability to execute without waiting for a natural final counterparty, supplied by intermediaries willing to temporarily bear risk.

## `dealer_price_impact`

- source_id: `kyle_1985`
- state: `defined`

The relationship between trading/order-flow pressure and price adjustment in a market where information is incorporated over time. Market depth/liquidity and informational impact are explicit model objects in Kyle's framework.

Project boundary: no universal XAUUSD coefficient is inferred from the theory paper.

## Operationalization status

All six concepts are **defined only**. None is `operational` because no project-approved observable proxy, lookback, trigger, threshold, invalidation, or execution rule has yet been frozen.
