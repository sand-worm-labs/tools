# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAIN = "{{chain}}"
TOKEN_ADDRESS = "{{token_address}}".strip()
FROM_DATE = "{{from_date}}".strip()
TO_DATE = "{{to_date}}".strip()
BUY_OR_SELL = "{{buy_or_sell}}".strip()
INCLUDE_LABELS = "{{include_labels}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}".strip()
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {"base", "bnb", "ethereum", "solana"}
ALLOWED_DIRECTIONS = {"BUY", "SELL"}
ALLOWED_LABELS = {
    "30D Smart Trader", "90D Smart Trader", "180D Smart Trader", "Fund", "Smart Trader",
    "Smart Dex Trader", "30D Smart Dex Trader", "90D Smart Dex Trader",
    "180D Smart Dex Trader", "Public Figure", "Exchange", "Whale", "BananaGun Bot User",
    "Top Maestro Bot User", "Top BananaGun Bot User", "Maestro Bot User",
    "Early MAGIC Miner", "First Mover LP", "First Mover Staking", "Profitable LP",
    "Smart HL Perps Trader",
}
ALLOWED_SORT_FIELDS = {"bought_volume_usd", "sold_volume_usd", "gross_volume_usd"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")
if not FROM_DATE or not TO_DATE:
    raise ValueError("from_date and to_date are required")
if BUY_OR_SELL and BUY_OR_SELL not in ALLOWED_DIRECTIONS:
    raise ValueError(f"Unsupported buy_or_sell: {BUY_OR_SELL!r}")
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
if BUY_OR_SELL:
    body["buy_or_sell"] = BUY_OR_SELL

filters = {}
if labels:
    filters["include_labels"] = labels
if filters:
    body["filters"] = filters

if SORT_FIELD:
    body["order_by"] = [{"field": SORT_FIELD, "direction": SORT_DIRECTION}]

response = requests.post(
    "https://api.nansen.ai/api/v1beta1/tgm/historical-who-bought-sold",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    # Net direction crossed with the smart-money flag separates "smart money driving
    # this" from "retail driving this" — neither bought/sold volume alone shows that.
    net_usd = {{__df_name}}["bought_volume_usd"] - {{__df_name}}["sold_volume_usd"]
    {{__df_name}}["net_volume_usd"] = net_usd
    {{__df_name}}["trader_signal"] = pd.Series(
        [
            ("smart_" if sm else "retail_") + ("accumulator" if n >= 0 else "distributor")
            for sm, n in zip({{__df_name}}["is_smart_money"], net_usd)
        ],
        index={{__df_name}}.index,
    )
    {{__df_name}} = {{__df_name}}.sort_values("net_volume_usd", key=abs, ascending=False).reset_index(drop=True)

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.head(25),
        x="address",
        y="net_volume_usd",
        color="trader_signal",
        title="Net buy/sell volume by trader (USD)",
    )
    fig.show()

{{__df_name}}
