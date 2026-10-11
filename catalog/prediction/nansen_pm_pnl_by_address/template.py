# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

ADDRESS = "{{address}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_DIRECTION = "{{sort_direction}}"

if not (1 <= len(ADDRESS) <= 100):
    raise ValueError("address must be 1-100 characters")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

body = {
    "address": ADDRESS,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": "total_pnl_usd", "direction": SORT_DIRECTION}],
}

response = requests.post(
    "https://api.nansen.ai/api/v1/prediction-market/pnl-by-address",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

payload = response.json()
{{__df_name}} = pd.DataFrame(payload.get("data", []))
has_full_history = bool(payload.get("pagination", {}).get("is_last_page"))

if not {{__df_name}}.empty:
    {{__df_name}}["roi_pct"] = (
        {{__df_name}}["total_pnl_usd"] / {{__df_name}}["net_buy_cost_usd"].replace(0, pd.NA) * 100
    )
    {{__df_name}}["pnl_rank"] = {{__df_name}}["total_pnl_usd"].rank(ascending=False, method="min").astype(int)
    # A partial page is sorted by PnL, so its win rate would be inflated — only
    # judge the wallet when every market it traded is in this response.
    if has_full_history:
        win_rate_pct = ({{__df_name}}["total_pnl_usd"] > 0).mean() * 100
        {{__df_name}}["win_rate_pct"] = win_rate_pct
        {{__df_name}}["small_sample_win_rate"] = (win_rate_pct > 70) and (len({{__df_name}}) < 5)
    else:
        {{__df_name}}["win_rate_pct"] = pd.NA
        {{__df_name}}["small_sample_win_rate"] = pd.NA
    {{__df_name}} = {{__df_name}}.sort_values("total_pnl_usd", ascending=False).reset_index(drop=True)

    import plotly.express as px

    fig = px.bar({{__df_name}}.head(25), x="question", y="total_pnl_usd", title="PnL by market for address")
    fig.show()

{{__df_name}}
