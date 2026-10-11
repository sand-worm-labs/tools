# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAINS = "{{chains}}"
TO_DATE = "{{to_date}}".strip()
TIMEFRAME_DAYS = "{{timeframe_days}}".strip()
TRADER_TYPE = "{{trader_type}}".strip()
SM_LABEL_FILTER = "{{sm_label_filter}}".strip()
EXCLUDE_SECTORS = "{{exclude_sectors}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}".strip()
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "arbitrum", "arc", "avalanche", "base", "bitcoin", "bnb", "citrea", "ethereum",
    "hyperevm", "injective", "iotaevm", "linea", "mantle", "mantra", "monad", "near",
    "optimism", "plasma", "polygon", "robinhood", "sei", "solana", "sonic",
    "starknet", "sui", "ton", "tron",
}
ALLOWED_TRADER_TYPES = {
    "all", "sm", "whale", "public_figure", "trending",
    "consistent_perps_winner", "high_winrate_hl_perps_trader", "predicted_winner",
}
ALLOWED_SM_LABELS = {
    "Fund", "Smart Trader", "30D Smart Trader", "90D Smart Trader", "180D Smart Trader",
    "Smart Dex Trader", "30D Smart Dex Trader", "90D Smart Dex Trader",
    "180D Smart Dex Trader", "Smart HL Perps Trader",
}
ALLOWED_SORT_FIELDS = {
    "volume", "buy_volume", "sell_volume", "netflow", "price_change", "market_cap_usd",
    "fdv", "liquidity", "price_usd", "nof_traders", "nof_buyers", "nof_sellers",
    "nof_buys", "nof_sells", "token_age_days",
}

chains = [c.strip() for c in CHAINS.split(",") if c.strip()]
if not chains:
    raise ValueError("chains is required")
for c in chains:
    if c not in ALLOWED_CHAINS:
        raise ValueError(f"Unsupported chain: {c!r}")
if not TO_DATE:
    raise ValueError("to_date is required")
if not TIMEFRAME_DAYS.isdigit() or not (1 <= int(TIMEFRAME_DAYS) <= 365):
    raise ValueError(f"Invalid timeframe_days: {TIMEFRAME_DAYS!r}")
if TRADER_TYPE and TRADER_TYPE not in ALLOWED_TRADER_TYPES:
    raise ValueError(f"Unsupported trader_type: {TRADER_TYPE!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD and SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

sm_labels = [label.strip() for label in SM_LABEL_FILTER.split(",") if label.strip()]
for label in sm_labels:
    if label not in ALLOWED_SM_LABELS:
        raise ValueError(f"Unsupported smart money label: {label!r}")

exclude_sectors = [s.strip() for s in EXCLUDE_SECTORS.split(",") if s.strip()]

body = {
    "to_date": TO_DATE,
    "timeframe_days": int(TIMEFRAME_DAYS),
    "chains": chains,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
}
if TRADER_TYPE:
    body["trader_type"] = TRADER_TYPE

filters = {}
if sm_labels:
    filters["sm_label_filter"] = sm_labels
if exclude_sectors:
    filters["exclude_sectors"] = exclude_sectors
if filters:
    body["filters"] = filters

if SORT_FIELD:
    body["order_by"] = [{"field": SORT_FIELD, "direction": SORT_DIRECTION}]

response = requests.post(
    "https://api.nansen.ai/api/v1beta1/token-screener/historical",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    {{__df_name}}["netflow_pct_mcap"] = (
        {{__df_name}}["netflow"] / {{__df_name}}["market_cap_usd"].replace(0, pd.NA) * 100
    )
    {{__df_name}}["buy_sell_ratio"] = {{__df_name}}["buy_volume"] / {{__df_name}}["sell_volume"].replace(0, pd.NA)
    {{__df_name}}["flow_signal"] = pd.cut(
        {{__df_name}}["buy_sell_ratio"],
        bins=[-float("inf"), 0.67, 1.5, float("inf")],
        labels=["net_selling", "balanced", "net_buying"],
    )
    {{__df_name}} = {{__df_name}}.sort_values("netflow_pct_mcap", ascending=False, na_position="last").reset_index(drop=True)

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.head(25),
        x="token_symbol",
        y="netflow_pct_mcap",
        color="flow_signal",
        title="Historical netflow intensity (% of market cap)",
    )
    fig.show()

{{__df_name}}
