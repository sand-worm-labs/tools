# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

ADDRESS = "{{address}}".strip()
TOKEN_SYMBOL = "{{token_symbol}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_SORT_FIELDS = {
    "leverage_value", "position_value_usd", "entry_price_usd",
    "liquidation_price_usd", "unrealized_pnl_usd", "size",
    "token_symbol", "position_type",
}

if len(ADDRESS) != 42 or not ADDRESS.startswith("0x"):
    raise ValueError(f"address must be a 42-character 0x-prefixed hex address: {ADDRESS!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

filters = {}
if TOKEN_SYMBOL:
    filters["token_symbol"] = TOKEN_SYMBOL

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

asset_positions = response.json().get("data", {}).get("assetPositions", [])
rows = []
for asset_position in asset_positions:
    position = dict(asset_position.get("position", {}))
    position["position_type"] = asset_position.get("position_type")
    rows.append(position)

{{__df_name}} = pd.DataFrame(rows)

if not {{__df_name}}.empty:
    for col in ("size", "entry_price_usd", "liquidation_price_usd", "position_value_usd", "unrealized_pnl_usd"):
        {{__df_name}}[col] = pd.to_numeric({{__df_name}}[col], errors="coerce")

    # Hyperliquid signs size by direction: positive is long, negative is short.
    {{__df_name}}["side"] = {{__df_name}}["size"].apply(lambda s: "long" if s >= 0 else "short")
    {{__df_name}}["distance_to_liquidation_pct"] = (
        ({{__df_name}}["entry_price_usd"] - {{__df_name}}["liquidation_price_usd"]).abs()
        / {{__df_name}}["entry_price_usd"] * 100
    )
    {{__df_name}}["unrealized_pnl_pct_of_position"] = (
        {{__df_name}}["unrealized_pnl_usd"] / {{__df_name}}["position_value_usd"] * 100
    )
    {{__df_name}} = {{__df_name}}.sort_values("distance_to_liquidation_pct", ascending=True).reset_index(drop=True)

    import plotly.express as px

    fig = px.bar(
        {{__df_name}},
        x="token_symbol",
        y="position_value_usd",
        color="side",
        title=f"Open perp positions for {ADDRESS}",
    )
    fig.show()

{{__df_name}}
