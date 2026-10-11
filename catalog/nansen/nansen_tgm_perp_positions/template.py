# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

TOKEN_SYMBOL = "{{token_symbol}}".strip()
LABEL_TYPE = "{{label_type}}"
SIDE = "{{side}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_LABEL_TYPES = {"smart_money", "all_traders", "whale", "public_figure"}
ALLOWED_SORT_FIELDS = {
    "address", "address_label", "side", "position_value_usd", "position_size",
    "size_base", "leverage", "entry_price", "mark_price", "liquidation_price",
    "funding_usd", "upnl_usd",
}

if not TOKEN_SYMBOL:
    raise ValueError("token_symbol is required")
if LABEL_TYPE not in ALLOWED_LABEL_TYPES:
    raise ValueError(f"Unsupported label_type: {LABEL_TYPE!r}")
if SIDE and SIDE not in {"Long", "Short"}:
    raise ValueError(f"Unsupported side: {SIDE!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

body = {
    "token_symbol": TOKEN_SYMBOL,
    "label_type": LABEL_TYPE,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if SIDE:
    body["filters"] = {"side": SIDE}

response = requests.post(
    "https://api.nansen.ai/api/v1/tgm/perp-positions",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    # Liquidation price alone doesn't say how close that is to the current
    # market — expressing the gap as a % of mark price makes positions on
    # wildly different tokens/sizes comparable, and flags real cascade risk.
    {{__df_name}}["liquidation_distance_pct"] = (
        ({{__df_name}}["mark_price"] - {{__df_name}}["liquidation_price"]).abs()
        / {{__df_name}}["mark_price"].replace(0, pd.NA) * 100
    )
    {{__df_name}}["liquidation_risk_flag"] = {{__df_name}}["liquidation_distance_pct"] <= 10

    import plotly.express as px

    fig = px.scatter(
        {{__df_name}}, x="liquidation_distance_pct", y="position_value_usd", color="side",
        title=f"Position size vs. liquidation distance — {TOKEN_SYMBOL}",
    )
    fig.show()

{{__df_name}}
