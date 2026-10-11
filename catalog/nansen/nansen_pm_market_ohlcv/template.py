# Sandworm Power Toolbox — {{__tool_name}}
import json
import os
import re

import pandas as pd
import requests

MARKET_ID = "{{market_id}}".strip()
DATE_RANGE = json.loads("""{{date_range}}""")
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_SORT_FIELDS = {"period_start", "volume_usd", "trade_count"}
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
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

body = {
    "market_id": MARKET_ID,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
date_filter = {}
if FROM_DATE:
    date_filter["from"] = FROM_DATE
if TO_DATE:
    date_filter["to"] = TO_DATE
if date_filter:
    body["date"] = date_filter

response = requests.post(
    "https://api.nansen.ai/api/v1/prediction-market/ohlcv",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    {{__df_name}} = {{__df_name}}.sort_values("period_start").reset_index(drop=True)
    {{__df_name}}["implied_probability_pct"] = {{__df_name}}["close"] * 100
    {{__df_name}}["period_return_pct"] = (
        ({{__df_name}}["close"] - {{__df_name}}["open"]) / {{__df_name}}["open"].replace(0, pd.NA) * 100
    )
    {{__df_name}}["volatility_close_std"] = {{__df_name}}["close"].std()
    {{__df_name}}["probability_change_over_window_pct"] = (
        ({{__df_name}}["close"].iloc[-1] - {{__df_name}}["close"].iloc[0]) * 100
    )
    {{__df_name}}["fragile_move"] = (
        {{__df_name}}["period_return_pct"].abs() > {{__df_name}}["period_return_pct"].abs().median()
    ) & ({{__df_name}}["volume_usd"] < {{__df_name}}["volume_usd"].median())

    import plotly.express as px

    fig = px.line({{__df_name}}, x="period_start", y="implied_probability_pct", title="Implied probability over time")
    fig.show()

{{__df_name}}
