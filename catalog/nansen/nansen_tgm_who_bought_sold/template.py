# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAIN = "{{chain}}".strip()
TOKEN_ADDRESS = "{{token_address}}".strip()
DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()
BUY_OR_SELL = "{{buy_or_sell}}"
INCLUDE_LABELS = "{{include_smart_money_labels}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "hyperevm",
    "hyperliquid", "injective", "iotaevm", "linea", "mantle", "mantra", "monad",
    "near", "optimism", "plasma", "polygon", "robinhood", "sei", "solana",
    "sonic", "starknet", "sui", "ton", "tron",
}
ALLOWED_LABELS = {
    "30D Smart Trader", "90D Smart Trader", "180D Smart Trader", "Fund",
    "Smart Trader", "Public Figure", "Exchange", "Whale", "BananaGun Bot User",
    "Top Maestro Bot User", "Top BananaGun Bot User", "Maestro Bot User",
    "Early MAGIC Miner", "First Mover LP", "First Mover Staking",
    "Profitable LP", "Smart HL Perps Trader",
}
ALLOWED_SORT_FIELDS = {
    "bought_volume_usd", "sold_volume_usd", "token_trade_volume",
    "trade_volume_usd", "bought_token_volume", "sold_token_volume",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")
if not DATE_FROM or not DATE_TO:
    raise ValueError("date_from and date_to are required")
if BUY_OR_SELL not in {"BUY", "SELL"}:
    raise ValueError(f"Unsupported buy_or_sell: {BUY_OR_SELL!r}")
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

body = {
    "chain": CHAIN,
    "token_address": TOKEN_ADDRESS,
    "date": {"from": DATE_FROM, "to": DATE_TO},
    "buy_or_sell": BUY_OR_SELL,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if labels:
    body["filters"] = {"include_smart_money_labels": labels}

response = requests.post(
    "https://api.nansen.ai/api/v1/tgm/who-bought-sold",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    {{__df_name}}["net_volume_usd"] = {{__df_name}}["bought_volume_usd"] - {{__df_name}}["sold_volume_usd"]
    {{__df_name}}["buy_sell_ratio"] = (
        {{__df_name}}["bought_volume_usd"] / {{__df_name}}["sold_volume_usd"].replace(0, pd.NA)
    )

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.head(25), x="address", y="trade_volume_usd", color="net_volume_usd",
        title=f"Top {BUY_OR_SELL.lower()}ers — {TOKEN_ADDRESS}",
    )
    fig.show()

{{__df_name}}
