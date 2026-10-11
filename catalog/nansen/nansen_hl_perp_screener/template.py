# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

FROM_DATE = "{{from_date}}".strip()
TO_DATE = "{{to_date}}".strip()
TRADER_TYPE = "{{trader_type}}"
TOKEN_SYMBOL = "{{token_symbol}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"
MIN_OPEN_INTEREST = "{{min_open_interest}}".strip()

ALLOWED_TRADER_TYPES = {"all", "sm", "whale", "public_figure", "high_winrate_hl_perps_trader"}
# Union of sort fields across trader_type variants — the API validates the exact
# field/trader_type combination, this just screens out obvious typos.
ALLOWED_SORT_FIELDS = {
    "token_symbol", "volume", "buy_volume", "sell_volume", "buy_sell_pressure",
    "trader_count", "mark_price", "funding", "previous_price_usd", "price_change",
    "open_interest", "smart_money_volume", "smart_money_buy_volume",
    "smart_money_sell_volume", "net_position_change",
    "current_smart_money_position_longs_usd", "current_smart_money_position_shorts_usd",
    "smart_money_longs_count", "smart_money_shorts_count",
    "current_position_longs_usd", "current_position_shorts_usd",
    "longs_count", "shorts_count",
}

if not FROM_DATE:
    raise ValueError("from_date is required")
if not TO_DATE:
    raise ValueError("to_date is required")
if TRADER_TYPE not in ALLOWED_TRADER_TYPES:
    raise ValueError(f"Unsupported trader_type: {TRADER_TYPE!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

filters = {"trader_type": TRADER_TYPE}
if TOKEN_SYMBOL:
    filters["token_symbol"] = TOKEN_SYMBOL
if MIN_OPEN_INTEREST:
    filters["open_interest"] = {"min": float(MIN_OPEN_INTEREST)}

body = {
    "date": {"from": FROM_DATE, "to": TO_DATE},
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "filters": filters,
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}

response = requests.post(
    "https://api.nansen.ai/api/v1/perp-screener",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

# "all" reports net taker flow as buy_sell_pressure; every other trader_type
# reports it as net_position_change. Either way it's the same kind of number.
FLOW_COL = "buy_sell_pressure" if "buy_sell_pressure" in {{__df_name}}.columns else "net_position_change"

if not {{__df_name}}.empty and FLOW_COL in {{__df_name}}.columns and "price_change" in {{__df_name}}.columns:
    # Divergence: order flow that disagrees with the price move it coincided
    # with is a read neither field shows alone — net buying while price falls
    # is accumulation into weakness, net selling while price rises is
    # distribution into strength.
    def _divergence(row):
        flow, price_change = row[FLOW_COL], row["price_change"]
        if pd.isna(flow) or pd.isna(price_change):
            return "unknown"
        if flow > 0 and price_change < 0:
            return "buying_into_weakness"
        if flow < 0 and price_change > 0:
            return "selling_into_strength"
        if flow > 0 and price_change > 0:
            return "confirmed_up"
        if flow < 0 and price_change < 0:
            return "confirmed_down"
        return "flat"

    {{__df_name}}["flow_price_divergence"] = {{__df_name}}.apply(_divergence, axis=1)

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.reindex({{__df_name}}[FLOW_COL].abs().sort_values(ascending=False).index).head(25),
        x="token_symbol",
        y=FLOW_COL,
        color="flow_price_divergence",
        title="Hyperliquid perps: order flow vs. price divergence",
    )
    fig.show()

{{__df_name}}
