# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAIN = "{{chain}}".strip()
TOKEN_ADDRESS = "{{token_address}}".strip()
DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "hyperevm",
    "hyperliquid", "linea", "mantle", "monad", "optimism", "plasma", "polygon",
    "robinhood", "sei", "solana", "sonic", "sui",
}
ALLOWED_SORT_FIELDS = {
    "pnl_usd_realised", "pnl_usd_unrealised", "pnl_usd_total", "roi_percent_total",
    "roi_percent_realised", "roi_percent_unrealised", "holding_amount", "holding_usd",
    "max_balance_held", "max_balance_held_usd", "still_holding_balance_ratio",
    "netflow_amount_usd", "netflow_amount", "nof_trades",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")
if not DATE_FROM or not DATE_TO:
    raise ValueError("date_from and date_to are required")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

body = {
    "chain": CHAIN,
    "token_address": TOKEN_ADDRESS,
    "date": {"from": DATE_FROM, "to": DATE_TO},
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}

response = requests.post(
    "https://api.nansen.ai/api/v1/tgm/pnl-leaderboard",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    # Winning vs. losing is one axis; still holding vs. already exited is another —
    # together they say whether winners have conviction or are cashing out, which
    # neither PnL nor holding ratio shows alone.
    winning = {{__df_name}}["pnl_usd_total"] > 0
    holding = {{__df_name}}["still_holding_balance_ratio"] >= 0.5
    {{__df_name}}["profit_conviction"] = [
        "winning_and_holding" if w and h
        else "winning_and_exited" if w and not h
        else "losing_and_holding" if not w and h
        else "losing_and_exited"
        for w, h in zip(winning, holding)
    ]

    import plotly.express as px

    fig = px.scatter(
        {{__df_name}}, x="still_holding_balance_ratio", y="roi_percent_total",
        color="profit_conviction", hover_name="trader_address",
        title=f"Trader PnL vs. conviction — {TOKEN_ADDRESS}",
    )
    fig.show()

{{__df_name}}
