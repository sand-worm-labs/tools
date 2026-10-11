# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

LOOKBACK_HOURS = "{{lookback_hours}}".strip()
TOKEN_SYMBOL = "{{token_symbol}}".strip()
SIDE = "{{side}}".strip()
ACTION = "{{action}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_SIDES = {"Long", "Short"}
ALLOWED_ACTIONS = {
    "Buy - Add Long", "Buy - Reduce Short", "Buy - Open Long", "Buy - Close Short",
    "Sell - Add Short", "Sell - Reduce Long", "Sell - Open Short", "Sell - Close Long",
}
ALLOWED_SORT_FIELDS = {"block_timestamp", "token_amount", "price_usd", "value_usd"}

if not LOOKBACK_HOURS.isdigit() or not (1 <= int(LOOKBACK_HOURS) <= 168):
    raise ValueError(f"Invalid lookback_hours: {LOOKBACK_HOURS!r}")
if SIDE and SIDE not in ALLOWED_SIDES:
    raise ValueError(f"Unsupported side: {SIDE!r}")
if ACTION and ACTION not in ALLOWED_ACTIONS:
    raise ValueError(f"Unsupported action: {ACTION!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

filters = {}
if TOKEN_SYMBOL:
    filters["token_symbol"] = TOKEN_SYMBOL
if SIDE:
    filters["side"] = SIDE
if ACTION:
    filters["action"] = ACTION

body = {
    "lookback_hours": int(LOOKBACK_HOURS),
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if filters:
    body["filters"] = filters

response = requests.post(
    "https://api.nansen.ai/api/v1/smart-money/perp-trades",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    # Net smart money positioning per token: the raw feed is per-trade, so
    # whether smart money is net accumulating or distributing a token only
    # shows up once action direction (Buy/Sell) and trade value are combined
    # and summed across trades.
    {{__df_name}}["directional_value_usd"] = {{__df_name}}.apply(
        lambda row: row["value_usd"] if str(row["action"]).startswith("Buy") else -row["value_usd"],
        axis=1,
    )

    net_flow_by_token = {{__df_name}}.groupby("token_symbol")["directional_value_usd"].sum().reset_index()

    import plotly.express as px

    fig = px.bar(
        net_flow_by_token.sort_values("directional_value_usd", key=abs, ascending=False).head(25),
        x="token_symbol",
        y="directional_value_usd",
        title="Smart money net positioning by token (buy value minus sell value)",
    )
    fig.show()

{{__df_name}}
