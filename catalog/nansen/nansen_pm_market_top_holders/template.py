# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

MARKET_ID = "{{market_id}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_SORT_FIELDS = {"position_size", "unrealized_pnl_usd", "avg_entry_price"}

if not (1 <= len(MARKET_ID) <= 100):
    raise ValueError("market_id must be 1-100 characters")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

body = {
    "market_id": MARKET_ID,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}

response = requests.post(
    "https://api.nansen.ai/api/v1/prediction-market/top-holders",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    {{__df_name}}["position_share_pct"] = (
        {{__df_name}}["position_size"] / {{__df_name}}["position_size"].sum() * 100
    )
    {{__df_name}}["unrealized_pnl_pct"] = {{__df_name}}["unrealized_pnl_usd"] / (
        {{__df_name}}["position_size"] * {{__df_name}}["avg_entry_price"]
    ).replace(0, pd.NA) * 100
    side_totals = {{__df_name}}.groupby("side")["position_size"].transform("sum")
    {{__df_name}}["side_share_pct"] = {{__df_name}}["position_size"] / side_totals.replace(0, pd.NA) * 100

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.head(25), x="address", y="position_size", color="side", title="Top holders by position size"
    )
    fig.show()

{{__df_name}}
