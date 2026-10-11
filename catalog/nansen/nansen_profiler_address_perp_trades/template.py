# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

ADDRESS = "{{address}}".strip()
DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()
TOKEN_SYMBOL = "{{token_symbol}}".strip()
SIDE = "{{side}}".strip()
ACTION = "{{action}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_DIRECTION = "{{sort_direction}}"

if not ADDRESS.startswith("0x") or len(ADDRESS) != 42:
    raise ValueError("address must be a 42-character hexadecimal Hyperliquid address")
if not DATE_FROM or not DATE_TO:
    raise ValueError("date_from and date_to are required")
if SIDE and SIDE not in {"Long", "Short"}:
    raise ValueError(f"Unsupported side: {SIDE!r}")
if ACTION and ACTION not in {"Open/Add", "Close/Reduce", "Liquidation"}:
    raise ValueError(f"Unsupported action: {ACTION!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
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
    "address": ADDRESS,
    "date": {"from": DATE_FROM, "to": DATE_TO},
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": "timestamp", "direction": SORT_DIRECTION}],
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

# closed_pnl alone overstates the result of a trade — fees are a separate
# field, and netting them out (then carrying a running total) is the actual
# economic PnL trend, which isn't a field Nansen returns directly.
if not {{__df_name}}.empty:
    {{__df_name}} = {{__df_name}}.sort_values("timestamp").reset_index(drop=True)
    {{__df_name}}["net_pnl_after_fees"] = {{__df_name}}["closed_pnl"] - {{__df_name}}["fee_usd"]
    {{__df_name}}["cumulative_net_pnl_usd"] = {{__df_name}}["net_pnl_after_fees"].cumsum()

    import plotly.express as px

    fig = px.line(
        {{__df_name}},
        x="timestamp",
        y="cumulative_net_pnl_usd",
        title="Cumulative perp PnL after fees",
    )
    fig.show()

{{__df_name}}
