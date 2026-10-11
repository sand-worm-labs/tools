# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

MARKET_ID = "{{market_id}}".strip()
PER_PAGE = "{{per_page}}".strip()

if not (1 <= len(MARKET_ID) <= 100):
    raise ValueError("market_id must be 1-100 characters")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")

body = {
    "market_id": MARKET_ID,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
}

response = requests.post(
    "https://api.nansen.ai/api/v1/prediction-market/position-detail",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    {{__df_name}}["pnl_pct"] = {{__df_name}}["token_pnl_usd"] / {{__df_name}}["buy_cost_usd"].replace(0, pd.NA) * 100
    outcome_totals = {{__df_name}}.groupby("outcome")["balance"].transform("sum")
    {{__df_name}}["position_share_of_outcome_pct"] = {{__df_name}}["balance"] / outcome_totals.replace(0, pd.NA) * 100
    {{__df_name}} = {{__df_name}}.sort_values("balance", ascending=False).reset_index(drop=True)

    import plotly.express as px

    fig = px.bar({{__df_name}}.head(25), x="address", y="balance", color="outcome", title="Top positions by balance")
    fig.show()

{{__df_name}}
