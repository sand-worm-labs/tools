# Sandworm Power Toolbox — {{__tool_name}}
import json
import os
import re

import pandas as pd
import requests

MARKET_ID = "{{market_id}}".strip()
DATE_RANGE = json.loads("""{{date_range}}""")
PER_PAGE = "{{per_page}}".strip()
SORT_DIRECTION = "{{sort_direction}}"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}Z?)?$")

if not (1 <= len(MARKET_ID) <= 100):
    raise ValueError("market_id must be 1-100 characters")

FROM_DATE = str(DATE_RANGE.get("from", "")).strip()
TO_DATE = str(DATE_RANGE.get("to", "")).strip()
if FROM_DATE and not DATE_RE.match(FROM_DATE):
    raise ValueError(f"Invalid date_range.from: {FROM_DATE!r}")
if TO_DATE and not DATE_RE.match(TO_DATE):
    raise ValueError(f"Invalid date_range.to: {TO_DATE!r}")

if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

body = {
    "market_id": MARKET_ID,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": "timestamp", "direction": SORT_DIRECTION}],
}
date_filter = {}
if FROM_DATE:
    date_filter["from"] = FROM_DATE
if TO_DATE:
    date_filter["to"] = TO_DATE
if date_filter:
    body["date"] = date_filter

response = requests.post(
    "https://api.nansen.ai/api/v1/prediction-market/trades-by-market",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    {{__df_name}} = {{__df_name}}.sort_values("timestamp").reset_index(drop=True)
    side_totals = {{__df_name}}.groupby("side")["usdc_value"].transform("sum")
    {{__df_name}}["side_volume_share_pct"] = side_totals / {{__df_name}}["usdc_value"].sum() * 100
    total_value = {{__df_name}}["usdc_value"].sum()
    top3_value = {{__df_name}}.nlargest(3, "usdc_value")["usdc_value"].sum()
    {{__df_name}}["large_trade_concentration_pct"] = top3_value / total_value * 100 if total_value else pd.NA

    import plotly.express as px

    fig = px.bar({{__df_name}}, x="timestamp", y="usdc_value", color="side", title="Trade volume by side over time")
    fig.show()

{{__df_name}}
