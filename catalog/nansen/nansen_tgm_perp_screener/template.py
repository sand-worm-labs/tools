# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()
TRADER_TYPE = "{{trader_type}}"
TOKEN_SYMBOL = "{{token_symbol}}".strip()
PER_PAGE = "{{per_page}}".strip()

ALLOWED_TRADER_TYPES = {"all", "sm", "whale", "public_figure", "high_winrate_hl_perps_trader"}

if not DATE_FROM or not DATE_TO:
    raise ValueError("date_from and date_to are required")
if TRADER_TYPE not in ALLOWED_TRADER_TYPES:
    raise ValueError(f"Unsupported trader_type: {TRADER_TYPE!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")

filters = {"trader_type": TRADER_TYPE}
if TOKEN_SYMBOL:
    filters["token_symbol"] = TOKEN_SYMBOL

body = {
    "date": {"from": DATE_FROM, "to": DATE_TO},
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "filters": filters,
    "include_price_change": TRADER_TYPE in {"whale", "public_figure", "high_winrate_hl_perps_trader"},
}

response = requests.post(
    "https://api.nansen.ai/api/v1/perp-screener",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    if TRADER_TYPE == "sm":
        {{__df_name}} = {{__df_name}}.rename(columns={
            "smart_money_volume": "volume",
            "smart_money_buy_volume": "buy_volume",
            "smart_money_sell_volume": "sell_volume",
            "current_smart_money_position_longs_usd": "current_position_longs_usd",
            "current_smart_money_position_shorts_usd": "current_position_shorts_usd",
            "smart_money_longs_count": "longs_count",
            "smart_money_shorts_count": "shorts_count",
        })

    flow_col = "buy_sell_pressure" if TRADER_TYPE == "all" else "net_position_change"

    # The flow column (order pressure or net positioning change) says which way
    # this cohort is leaning; price_change says what actually happened. When
    # they disagree — buying pressure with price falling, or selling with price
    # rising — that mismatch is the signal, not either column alone.
    flow_bullish = {{__df_name}}[flow_col] > 0
    price_up = {{__df_name}}["price_change"] > 0
    {{__df_name}}["flow_price_divergence"] = flow_bullish != price_up
    {{__df_name}}["divergence_magnitude"] = {{__df_name}}[flow_col].abs().where({{__df_name}}["flow_price_divergence"], 0)

    diverging = {{__df_name}}[{{__df_name}}["flow_price_divergence"]].sort_values("divergence_magnitude", ascending=False)
    if not diverging.empty:
        import plotly.express as px

        fig = px.bar(
            diverging.head(15), x="token_symbol", y="divergence_magnitude", color="price_change",
            title=f"Flow/price divergence — {TRADER_TYPE} cohort",
        )
        fig.show()

{{__df_name}}
