# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

MARKET_ID = "{{market_id}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_DIRECTION = "{{sort_direction}}"

if not (1 <= len(MARKET_ID) <= 100):
    raise ValueError("market_id must be 1-100 characters")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

body = {
    "market_id": MARKET_ID,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": "total_pnl_usd", "direction": SORT_DIRECTION}],
}

response = requests.post(
    "https://api.nansen.ai/api/v1/prediction-market/pnl-by-market",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    {{__df_name}}["roi_pct"] = (
        {{__df_name}}["total_pnl_usd"] / {{__df_name}}["net_buy_cost_usd"].replace(0, pd.NA) * 100
    )
    {{__df_name}}["pnl_rank"] = {{__df_name}}["total_pnl_usd"].rank(ascending=False, method="min").astype(int)
    {{__df_name}}["roi_tier"] = pd.cut(
        {{__df_name}}["roi_pct"],
        bins=[-float("inf"), 0, 50, 100, float("inf")],
        labels=["loss", "0-50%", "50-100%", ">100%"],
    )
    {{__df_name}} = {{__df_name}}.sort_values("total_pnl_usd", ascending=False).reset_index(drop=True)

    import plotly.express as px

    fig = px.bar({{__df_name}}.head(25), x="address", y="total_pnl_usd", color="roi_tier", title="Top traders by PnL")
    fig.show()

{{__df_name}}
