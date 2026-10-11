# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()
TRADER_ADDRESS_LABEL = "{{trader_address_label}}".strip()
INCLUDE_LABELS = "{{include_smart_money_labels}}".strip()
MIN_ROI = "{{min_roi}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_LABELS = {"Fund", "Smart Trader", "30D Smart Trader", "90D Smart Trader", "180D Smart Trader", "Smart HL Perps Trader"}
ALLOWED_SORT_FIELDS = {
    "total_pnl", "realized_pnl_usd", "unrealized_pnl_usd", "roi", "volume_usd",
    "total_trades", "account_value",
}

if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

labels = [label.strip() for label in INCLUDE_LABELS.split(",") if label.strip()]
for label in labels:
    if label not in ALLOWED_LABELS:
        raise ValueError(f"Unsupported smart money label: {label!r}")

date_range = {}
if DATE_FROM:
    date_range["from"] = DATE_FROM
if DATE_TO:
    date_range["to"] = DATE_TO

filters = {}
if TRADER_ADDRESS_LABEL:
    filters["trader_address_label"] = TRADER_ADDRESS_LABEL
if labels:
    filters["include_smart_money_labels"] = labels
if MIN_ROI:
    filters["roi"] = {"min": float(MIN_ROI)}

body = {
    "date": date_range,
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

# roi is PnL against account equity — it says nothing about how much of that
# PnL came from just trading a huge book. Netting PnL against volume instead
# shows the edge per dollar actually traded, separating size from skill.
if not {{__df_name}}.empty:
    {{__df_name}}["pnl_per_volume_pct"] = (
        {{__df_name}}["total_pnl"] / {{__df_name}}["volume_usd"].replace(0, pd.NA) * 100
    )

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.head(25),
        x="trader_address",
        y="total_pnl",
        color="pnl_per_volume_pct",
        title="Top traders by PnL, colored by edge per dollar traded",
    )
    fig.show()

{{__df_name}}
