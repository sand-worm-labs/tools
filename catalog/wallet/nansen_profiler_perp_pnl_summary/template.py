# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

ADDRESS = "{{address}}".strip()
DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()

if not ADDRESS.startswith("0x") or len(ADDRESS) != 42:
    raise ValueError("address must be a 42-character hexadecimal Hyperliquid address")

date_range = {}
if DATE_FROM:
    date_range["from"] = DATE_FROM
if DATE_TO:
    date_range["to"] = DATE_TO

body = {
    "address": ADDRESS,
    "date": date_range,
}

response = requests.post(
    "https://api.nansen.ai/api/v1/profiler/perp-pnl-summary",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

# This endpoint returns one account-level summary object, not a row list —
# the only per-row data is top5_coins, so that's what becomes the dataframe,
# with the account totals attached to each row for context.
summary = response.json().get("data", {})
{{__df_name}} = pd.DataFrame(summary.get("top5_coins", []))

if not {{__df_name}}.empty:
    account_realized_pnl_usd = summary.get("realized_pnl_usd", 0)
    {{__df_name}}["account_realized_pnl_usd"] = account_realized_pnl_usd
    {{__df_name}}["account_win_rate"] = summary.get("win_rate")

    # A coin's own realized_pnl_usd doesn't say whether it's the trader's
    # whole edge or a sliver of it — share of the account's total realized
    # PnL shows concentration vs breadth across the top coins.
    {{__df_name}}["pct_of_account_realized_pnl"] = (
        {{__df_name}}["realized_pnl_usd"] / account_realized_pnl_usd * 100 if account_realized_pnl_usd else pd.NA
    )

    import plotly.express as px

    fig = px.bar(
        {{__df_name}},
        x="coin",
        y="realized_pnl_usd",
        color="pct_of_account_realized_pnl",
        title="Top 5 coins by realized PnL, share of account total",
    )
    fig.show()

{{__df_name}}
