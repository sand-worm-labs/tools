# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

FROM_DATE = "{{from_date}}".strip()
TO_DATE = "{{to_date}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"
MIN_ROI = "{{min_roi}}".strip()

ALLOWED_SORT_FIELDS = {
    "total_pnl", "realized_pnl_usd", "unrealized_pnl_usd", "roi",
    "volume_usd", "total_trades", "account_value",
}

if not FROM_DATE:
    raise ValueError("from_date is required")
if not TO_DATE:
    raise ValueError("to_date is required")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

filters = {}
if MIN_ROI:
    filters["roi"] = {"min": float(MIN_ROI)}

body = {
    "date": {"from": FROM_DATE, "to": TO_DATE},
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if filters:
    body["filters"] = filters

response = requests.post(
    "https://api.nansen.ai/api/v1/perp-leaderboard",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    # Size-adjusted skill read: PnL earned per fill, not just total PnL (a trader
    # with 10x the trades isn't necessarily 10x better).
    {{__df_name}}["pnl_per_trade_usd"] = {{__df_name}}["total_pnl"] / {{__df_name}}["total_trades"].replace(0, pd.NA)
    # Conviction vs breadth: how much of the account is riding on its five biggest
    # bets, combining the nested top_positions with account_value — neither field
    # shows this alone.
    {{__df_name}}["top_position_concentration_pct"] = {{__df_name}}.apply(
        lambda row: sum(abs(p["position_value_usd"]) for p in row["top_positions"])
        / row["account_value"] * 100
        if row.get("account_value") else None,
        axis=1,
    )

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.head(25),
        x="trader_address",
        y="total_pnl",
        color="top_position_concentration_pct",
        title="Top Hyperliquid perp traders by PnL and position concentration",
    )
    fig.show()

{{__df_name}}
