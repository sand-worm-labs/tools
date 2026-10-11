# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

TOKEN_SYMBOL = "{{token_symbol}}".strip()
FROM_DATE = "{{from_date}}".strip()
TO_DATE = "{{to_date}}".strip()
SIDE = "{{side}}".strip()
ORDER_TYPE = "{{order_type}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_SIDES = {"Long", "Short"}
ALLOWED_ORDER_TYPES = {"MARKET", "LIMIT"}
ALLOWED_SORT_FIELDS = {"block_timestamp", "token_amount", "value_usd", "transaction_hash", "trader_address"}

if not TOKEN_SYMBOL:
    raise ValueError("token_symbol is required")
if not FROM_DATE:
    raise ValueError("from_date is required")
if not TO_DATE:
    raise ValueError("to_date is required")
if SIDE and SIDE not in ALLOWED_SIDES:
    raise ValueError(f"Unsupported side: {SIDE!r}")
if ORDER_TYPE and ORDER_TYPE not in ALLOWED_ORDER_TYPES:
    raise ValueError(f"Unsupported order_type: {ORDER_TYPE!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

filters = {}
if SIDE:
    filters["side"] = SIDE
if ORDER_TYPE:
    filters["order_type"] = ORDER_TYPE

body = {
    "token_symbol": TOKEN_SYMBOL,
    "date": {"from": FROM_DATE, "to": TO_DATE},
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if filters:
    body["filters"] = filters

response = requests.post(
    "https://api.nansen.ai/api/v1/tgm/perp-trades",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    # Crowd positioning trend: no single trade shows whether the whole trader
    # base has been net accumulating or distributing this token over the
    # window — only combining action direction with value and running a
    # cumulative sum in chronological order does.
    {{__df_name}}["directional_value_usd"] = {{__df_name}}.apply(
        lambda row: row["value_usd"] if str(row["action"]).startswith("Buy") else -row["value_usd"],
        axis=1,
    )
    chronological = {{__df_name}}.sort_values("block_timestamp").copy()
    chronological["cumulative_net_flow_usd"] = chronological["directional_value_usd"].cumsum()
    {{__df_name}} = {{__df_name}}.merge(chronological[["cumulative_net_flow_usd"]], left_index=True, right_index=True)

    import plotly.express as px

    fig = px.line(
        chronological,
        x="block_timestamp",
        y="cumulative_net_flow_usd",
        title=f"Cumulative net crowd flow for {TOKEN_SYMBOL} perps",
    )
    fig.show()

{{__df_name}}
