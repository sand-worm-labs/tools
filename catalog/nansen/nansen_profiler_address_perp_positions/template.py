# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

ADDRESS = "{{address}}".strip()
TOKEN_SYMBOL = "{{token_symbol}}".strip()
POSITION_TYPE = "{{position_type}}".strip()
MIN_POSITION_VALUE_USD = "{{min_position_value_usd}}".strip()
MAX_POSITION_VALUE_USD = "{{max_position_value_usd}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_SORT_FIELDS = {
    "leverage_value", "position_value_usd", "entry_price_usd",
    "liquidation_price_usd", "unrealized_pnl_usd", "size", "token_symbol",
    "position_type",
}

if not ADDRESS.startswith("0x") or len(ADDRESS) != 42:
    raise ValueError("address must be a 42-character hexadecimal Hyperliquid address")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

position_value_range = {}
if MIN_POSITION_VALUE_USD:
    position_value_range["min"] = float(MIN_POSITION_VALUE_USD)
if MAX_POSITION_VALUE_USD:
    position_value_range["max"] = float(MAX_POSITION_VALUE_USD)

filters = {}
if TOKEN_SYMBOL:
    filters["token_symbol"] = TOKEN_SYMBOL
if POSITION_TYPE:
    filters["position_type"] = POSITION_TYPE
if position_value_range:
    filters["position_value_usd"] = position_value_range

body = {
    "address": ADDRESS,
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if filters:
    body["filters"] = filters

response = requests.post(
    "https://api.nansen.ai/api/v1/profiler/perp-positions",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

# The response wraps a single account object (margin summary + positions)
# under "data", not a flat list — each open position's own dict is nested
# under assetPositions[i]["position"].
asset_positions = response.json().get("data", {}).get("assetPositions", [])
{{__df_name}} = pd.DataFrame(
    [{**p.get("position", {}), "position_type": p.get("position_type")} for p in asset_positions]
)

# Hyperliquid returns these as strings; numeric filters/signals need floats.
if not {{__df_name}}.empty:
    for col in ("position_value_usd", "entry_price_usd", "liquidation_price_usd", "unrealized_pnl_usd"):
        if col in {{__df_name}}.columns:
            {{__df_name}}[col] = pd.to_numeric({{__df_name}}[col], errors="coerce")

    # Leverage alone doesn't say how close a position is to being liquidated —
    # that depends on how far the entry price actually sits from the
    # liquidation price, which Nansen doesn't surface as a single number.
    {{__df_name}}["liq_distance_pct"] = (
        ({{__df_name}}["liquidation_price_usd"] - {{__df_name}}["entry_price_usd"]).abs()
        / {{__df_name}}["entry_price_usd"].replace(0, pd.NA)
        * 100
    )
    {{__df_name}}["risk_tier"] = pd.cut(
        {{__df_name}}["liq_distance_pct"],
        bins=[-float("inf"), 10, 30, float("inf")],
        labels=["high_risk", "moderate_risk", "low_risk"],
    )

    import plotly.express as px

    fig = px.bar(
        {{__df_name}},
        x="token_symbol",
        y="position_value_usd",
        color="risk_tier",
        title="Open perp positions by value and liquidation risk",
    )
    fig.show()

{{__df_name}}
