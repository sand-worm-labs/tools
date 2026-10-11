# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAINS = "{{chains}}"
TRADER_ADDRESS = "{{trader_address}}".strip()
TOKEN_BOUGHT_ADDRESS = "{{token_bought_address}}".strip()
INCLUDE_LABELS = "{{include_smart_money_labels}}".strip()
MIN_TRADE_VALUE_USD = "{{min_trade_value_usd}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "all", "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "hyperevm",
    "iotaevm", "linea", "mantle", "monad", "optimism", "plasma", "polygon",
    "robinhood", "sei", "solana", "sonic",
}
ALLOWED_LABELS = {"Fund", "Smart Trader", "30D Smart Trader", "90D Smart Trader", "180D Smart Trader", "Smart HL Perps Trader"}
ALLOWED_SORT_FIELDS = {"chain", "block_timestamp", "trade_value_usd", "token_bought_age_days", "token_bought_market_cap"}

chains = [c.strip() for c in CHAINS.split(",") if c.strip()]
if not chains:
    raise ValueError("chains is required")
for c in chains:
    if c not in ALLOWED_CHAINS:
        raise ValueError(f"Unsupported chain: {c!r}")
if MIN_TRADE_VALUE_USD and not MIN_TRADE_VALUE_USD.replace(".", "", 1).isdigit():
    raise ValueError(f"Invalid min_trade_value_usd: {MIN_TRADE_VALUE_USD!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

labels = [label.strip() for label in INCLUDE_LABELS.split(",") if label.strip()]
for label in labels:
    if label not in ALLOWED_LABELS:
        raise ValueError(f"Unsupported smart money label: {label!r}")

filters = {}
if TRADER_ADDRESS:
    filters["trader_address"] = TRADER_ADDRESS
if TOKEN_BOUGHT_ADDRESS:
    filters["token_bought_address"] = TOKEN_BOUGHT_ADDRESS
if labels:
    filters["include_smart_money_labels"] = labels
if MIN_TRADE_VALUE_USD:
    filters["trade_value_usd"] = {"min": float(MIN_TRADE_VALUE_USD)}

body = {
    "chains": chains,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if filters:
    body["filters"] = filters

response = requests.post(
    "https://api.nansen.ai/api/v1/smart-money/dex-trades",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

# bought_dilution_pct combines FDV and circulating market cap into a supply-
# overhang read a raw trade row doesn't give. early_conviction combines size
# (trade_value_usd) with how new the bought token is — a big ticket into a
# token days old reads very differently from the same ticket into a blue chip.
if not {{__df_name}}.empty:
    {{__df_name}}["bought_dilution_pct"] = (
        ({{__df_name}}["token_bought_fdv"] - {{__df_name}}["token_bought_market_cap"])
        / {{__df_name}}["token_bought_market_cap"].replace(0, pd.NA) * 100
    )

    median_value = {{__df_name}}["trade_value_usd"].median()
    median_age = {{__df_name}}["token_bought_age_days"].median()

    def _conviction(row):
        value, age = row.get("trade_value_usd"), row.get("token_bought_age_days")
        if pd.isna(value) or pd.isna(age):
            return "unknown"
        if value >= median_value and age <= median_age:
            return "high_conviction_early_bet"
        return "normal"

    {{__df_name}}["early_conviction"] = {{__df_name}}.apply(_conviction, axis=1)
    {{__df_name}} = {{__df_name}}.sort_values("trade_value_usd", ascending=False, na_position="last").reset_index(drop=True)

    import plotly.express as px

    fig = px.scatter(
        {{__df_name}},
        x="token_bought_age_days",
        y="trade_value_usd",
        color="early_conviction",
        hover_data=["token_bought_symbol", "trader_address_label"],
        title="Smart money DEX trades: size vs. bought-token age",
    )
    fig.show()

{{__df_name}}
