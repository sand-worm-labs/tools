# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

ADDRESS = "{{address}}".strip()
FROM_DATE = "{{from_date}}".strip()
TO_DATE = "{{to_date}}".strip()
TOKEN_SYMBOL = "{{token_symbol}}".strip()
SIDE = "{{side}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_SIDES = {"Long", "Short"}
ALLOWED_SORT_FIELDS = {"timestamp", "size", "fee_usd", "closed_pnl", "price", "value_usd"}

if len(ADDRESS) != 42 or not ADDRESS.startswith("0x"):
    raise ValueError(f"address must be a 42-character 0x-prefixed hex address: {ADDRESS!r}")
if SIDE and SIDE not in ALLOWED_SIDES:
    raise ValueError(f"Unsupported side: {SIDE!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

date_range = {}
if FROM_DATE:
    date_range["from"] = FROM_DATE
if TO_DATE:
    date_range["to"] = TO_DATE

filters = {}
if TOKEN_SYMBOL:
    filters["token_symbol"] = TOKEN_SYMBOL
if SIDE:
    filters["side"] = SIDE

body = {
    "address": ADDRESS,
    "date": date_range,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if filters:
    body["filters"] = filters

response = requests.post(
    "https://api.nansen.ai/api/v1/profiler/perp-trades",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    {{__df_name}}["net_pnl_usd"] = {{__df_name}}["closed_pnl"] - {{__df_name}}["fee_usd"]
    chronological = {{__df_name}}.sort_values("timestamp").copy()
    chronological["cumulative_net_pnl_usd"] = chronological["net_pnl_usd"].cumsum()
    {{__df_name}} = {{__df_name}}.merge(chronological[["cumulative_net_pnl_usd"]], left_index=True, right_index=True)

    import plotly.express as px

    fig = px.line(
        chronological,
        x="timestamp",
        y="cumulative_net_pnl_usd",
        color="side",
        title=f"Cumulative net PnL (after fees) for {ADDRESS}",
    )
    fig.show()

{{__df_name}}
