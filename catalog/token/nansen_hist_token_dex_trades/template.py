# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAIN = "{{chain}}"
TOKEN_ADDRESS = "{{token_address}}".strip()
FROM_DATE = "{{from_date}}".strip()
TO_DATE = "{{to_date}}".strip()
ACTION = "{{action}}".strip()
INCLUDE_LABELS = "{{include_labels}}".strip()
TRADER_ADDRESS = "{{trader_address}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}".strip()
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {"base", "bnb", "ethereum", "solana"}
ALLOWED_ACTIONS = {"BUY", "SELL"}
ALLOWED_LABELS = {
    "30D Smart Trader", "90D Smart Trader", "180D Smart Trader", "Fund", "Smart Trader",
    "Smart Dex Trader", "30D Smart Dex Trader", "90D Smart Dex Trader",
    "180D Smart Dex Trader", "Public Figure", "Exchange", "Whale", "BananaGun Bot User",
    "Top Maestro Bot User", "Top BananaGun Bot User", "Maestro Bot User",
    "Early MAGIC Miner", "First Mover LP", "First Mover Staking", "Profitable LP",
    "Smart HL Perps Trader",
}
ALLOWED_SORT_FIELDS = {"block_timestamp", "estimated_value_usd", "token_amount", "estimated_swap_price_usd"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")
if not FROM_DATE or not TO_DATE:
    raise ValueError("from_date and to_date are required")
if ACTION and ACTION not in ALLOWED_ACTIONS:
    raise ValueError(f"Unsupported action: {ACTION!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD and SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

labels = [label.strip() for label in INCLUDE_LABELS.split(",") if label.strip()]
for label in labels:
    if label not in ALLOWED_LABELS:
        raise ValueError(f"Unsupported trader label: {label!r}")

body = {
    "chain": CHAIN,
    "token_address": TOKEN_ADDRESS,
    "date_range": {"from": FROM_DATE, "to": TO_DATE},
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
}

filters = {}
if ACTION:
    filters["action"] = ACTION
if labels:
    filters["include_labels"] = labels
if TRADER_ADDRESS:
    filters["trader_address"] = TRADER_ADDRESS
if filters:
    body["filters"] = filters

if SORT_FIELD:
    body["order_by"] = [{"field": SORT_FIELD, "direction": SORT_DIRECTION}]

response = requests.post(
    "https://api.nansen.ai/api/v1beta1/tgm/historical-dex-trades",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    {{__df_name}}["trade_date"] = pd.to_datetime({{__df_name}}["block_timestamp"]).dt.date
    {{__df_name}}["signed_value_usd"] = {{__df_name}}["estimated_value_usd"].where(
        {{__df_name}}["action"] == "BUY", -{{__df_name}}["estimated_value_usd"]
    )

    import plotly.express as px

    daily_netflow = {{__df_name}}.groupby("trade_date")["signed_value_usd"].sum().reset_index()
    fig = px.bar(daily_netflow, x="trade_date", y="signed_value_usd", title="Daily net DEX flow (USD)")
    fig.show()

{{__df_name}}
