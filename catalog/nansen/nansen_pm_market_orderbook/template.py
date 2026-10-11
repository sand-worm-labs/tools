# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

MARKET_ID = "{{market_id}}".strip()
PER_PAGE = "{{per_page}}".strip()

if not (1 <= len(MARKET_ID) <= 100):
    raise ValueError("market_id must be 1-100 characters")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")

body = {
    "market_id": MARKET_ID,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
}

response = requests.post(
    "https://api.nansen.ai/api/v1/prediction-market/orderbook",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    bids = {{__df_name}}[{{__df_name}}["side"] == "buy"]
    asks = {{__df_name}}[{{__df_name}}["side"] == "sell"]
    best_bid = bids["price"].max() if not bids.empty else pd.NA
    best_ask = asks["price"].min() if not asks.empty else pd.NA
    bid_depth = bids["size"].sum()
    ask_depth = asks["size"].sum()

    {{__df_name}}["best_bid"] = best_bid
    {{__df_name}}["best_ask"] = best_ask
    {{__df_name}}["spread"] = best_ask - best_bid if pd.notna(best_bid) and pd.notna(best_ask) else pd.NA
    {{__df_name}}["mid_price_implied_probability_pct"] = (
        (best_bid + best_ask) / 2 * 100 if pd.notna(best_bid) and pd.notna(best_ask) else pd.NA
    )
    {{__df_name}}["depth_imbalance"] = (bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) else pd.NA

    total_size = {{__df_name}}["size"].sum()
    top3_size = {{__df_name}}.nlargest(3, "size")["size"].sum()
    {{__df_name}}["depth_concentration_top3_pct"] = top3_size / total_size * 100 if total_size else pd.NA

    import plotly.express as px

    fig = px.line({{__df_name}}, x="price", y="cumulative_size", color="side", title="Order book depth")
    fig.show()

{{__df_name}}
