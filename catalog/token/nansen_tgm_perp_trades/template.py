# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

TOKEN_SYMBOL = "{{token_symbol}}".strip()
DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()
SIDE = "{{side}}".strip()
INCLUDE_LABELS = "{{include_smart_money_labels}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_LABELS = {
    "Fund", "Smart Trader", "30D Smart Trader", "90D Smart Trader",
    "180D Smart Trader", "Smart HL Perps Trader",
}

if not TOKEN_SYMBOL:
    raise ValueError("token_symbol is required")
if SIDE and SIDE not in {"Long", "Short"}:
    raise ValueError(f"Unsupported side: {SIDE!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

labels = [label.strip() for label in INCLUDE_LABELS.split(",") if label.strip()]
for label in labels:
    if label not in ALLOWED_LABELS:
        raise ValueError(f"Unsupported smart money label: {label!r}")

filters = {}
if SIDE:
    filters["side"] = SIDE
if labels:
    filters["include_smart_money_labels"] = labels

date_range = {}
if DATE_FROM:
    date_range["from"] = DATE_FROM
if DATE_TO:
    date_range["to"] = DATE_TO

body = {
    "token_symbol": TOKEN_SYMBOL,
    "date": date_range,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": "block_timestamp", "direction": SORT_DIRECTION}],
}
if filters:
    body["filters"] = filters

response = requests.post(
    "https://api.nansen.ai/api/v1/tgm/perp-trades",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    {{__df_name}} = {{__df_name}}.sort_values("block_timestamp").reset_index(drop=True)

    # A Buy can either open a new long or close out a short — collapsing that
    # into a plain Buy/Sell net flow hides whether money is initiating fresh
    # conviction (Open/Close) or just resizing an existing bet (Add/Reduce).
    {{__df_name}}["position_effect"] = {{__df_name}}["action"].apply(
        lambda a: "open" if "Open" in a else ("close" if "Close" in a else "resize")
    )
    side_sign = {{__df_name}}["side"].map({"Long": 1, "Short": -1}).fillna(0)
    effect_sign = {{__df_name}}["position_effect"].map({"open": 1, "close": -1}).fillna(0)
    {{__df_name}}["net_new_exposure_usd"] = side_sign * effect_sign * {{__df_name}}["value_usd"]
    {{__df_name}}["cumulative_net_new_exposure_usd"] = {{__df_name}}["net_new_exposure_usd"].cumsum()

    import plotly.express as px

    fig = px.line(
        {{__df_name}}, x="block_timestamp", y="cumulative_net_new_exposure_usd",
        title=f"Net fresh long/short conviction — {TOKEN_SYMBOL}",
    )
    fig.show()

{{__df_name}}
