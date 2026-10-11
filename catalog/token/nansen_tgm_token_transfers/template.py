# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAIN = "{{chain}}".strip()
TOKEN_ADDRESS = "{{token_address}}".strip()
DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()
ONLY_SMART_MONEY = "{{only_smart_money}}"
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "arbitrum", "arc", "avalanche", "base", "bitcoin", "bnb", "ethereum",
    "hyperevm", "injective", "iotaevm", "linea", "mantle", "mantra", "monad",
    "near", "optimism", "plasma", "polygon", "robinhood", "sei", "solana",
    "sonic", "starknet", "sui", "ton", "tron",
}
ALLOWED_SORT_FIELDS = {
    "block_timestamp", "transaction_hash", "from_address", "to_address",
    "from_address_label", "to_address_label", "transaction_type",
    "transfer_amount", "transfer_value_usd",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")
if not DATE_FROM or not DATE_TO:
    raise ValueError("date_from and date_to are required")
if ONLY_SMART_MONEY not in {"true", "false"}:
    raise ValueError(f"Invalid only_smart_money: {ONLY_SMART_MONEY!r}")
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
    "filters": {"only_smart_money": ONLY_SMART_MONEY == "true"},
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}

response = requests.post(
    "https://api.nansen.ai/api/v1/tgm/transfers",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    pair_key = {{__df_name}}["from_address"] + "->" + {{__df_name}}["to_address"]
    pair_counts = pair_key.value_counts()
    {{__df_name}}["counterparty_repeat_count"] = pair_key.map(pair_counts)
    {{__df_name}}["repeated_counterparty_flag"] = {{__df_name}}["counterparty_repeat_count"] > 1

    repeated = {{__df_name}}[{{__df_name}}["repeated_counterparty_flag"]]
    if not repeated.empty:
        import plotly.express as px

        fig = px.bar(
            repeated.assign(pair=pair_key[repeated.index]),
            x="pair", y="transfer_value_usd",
            title=f"Repeated counterparty transfers — {TOKEN_ADDRESS}",
        )
        fig.show()

{{__df_name}}
