# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAIN = "{{chain}}".strip()
TOKEN_ADDRESS = "{{token_address}}".strip()
DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()
ONLY_SMART_MONEY = "{{only_smart_money}}"
ACTION = "{{action}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "hyperevm",
    "hyperliquid", "injective", "iotaevm", "linea", "mantle", "mantra", "monad",
    "near", "optimism", "plasma", "polygon", "robinhood", "sei", "solana",
    "sonic", "starknet", "sui", "ton", "tron",
}
ALLOWED_SORT_FIELDS = {
    "block_timestamp", "transaction_hash", "trader_address", "trader_address_label",
    "token_address", "action", "token_name", "token_amount", "traded_token_address",
    "traded_token_name", "traded_token_amount", "estimated_swap_price_usd",
    "estimated_value_usd",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")
if not DATE_FROM or not DATE_TO:
    raise ValueError("date_from and date_to are required")
if ONLY_SMART_MONEY not in {"true", "false"}:
    raise ValueError(f"Invalid only_smart_money: {ONLY_SMART_MONEY!r}")
if ACTION and ACTION not in {"BUY", "SELL"}:
    raise ValueError(f"Unsupported action: {ACTION!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

body = {
    "chain": CHAIN,
    "token_address": TOKEN_ADDRESS,
    "date": {"from": DATE_FROM, "to": DATE_TO},
    "only_smart_money": ONLY_SMART_MONEY == "true",
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if ACTION:
    body["filters"] = {"action": ACTION}

response = requests.post(
    "https://api.nansen.ai/api/v1/tgm/dex-trades",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    {{__df_name}} = {{__df_name}}.sort_values("block_timestamp").reset_index(drop=True)
    {{__df_name}}["signed_value_usd"] = {{__df_name}}.apply(
        lambda r: r["estimated_value_usd"] if r["action"] == "BUY" else -r["estimated_value_usd"], axis=1
    )
    {{__df_name}}["cumulative_net_flow_usd"] = {{__df_name}}["signed_value_usd"].cumsum()

    import plotly.express as px

    fig = px.line(
        {{__df_name}}, x="block_timestamp", y="cumulative_net_flow_usd",
        title=f"Cumulative net DEX flow — {TOKEN_ADDRESS}",
    )
    fig.show()

{{__df_name}}
