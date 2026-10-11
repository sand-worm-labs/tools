# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAIN = "{{chain}}"
TOKEN_ADDRESS = "{{token_address}}".strip()
FROM_DATE = "{{from_date}}".strip()
TO_DATE = "{{to_date}}".strip()
TRADER_ADDRESS = "{{trader_address}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}".strip()
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {"base", "bnb", "ethereum", "solana"}
ALLOWED_SORT_FIELDS = {
    "pnl_usd_total", "roi_percent_total", "pnl_usd_realised", "roi_percent_realised",
    "pnl_usd_unrealised", "roi_percent_unrealised", "holding_usd", "holding_amount",
    "nof_trades", "still_holding_balance_ratio", "netflow_amount_usd", "max_balance_held",
    "max_balance_held_usd", "nof_buys", "nof_sells", "bought_amount", "sold_amount",
    "bought_usd", "sold_usd",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")
if not FROM_DATE or not TO_DATE:
    raise ValueError("from_date and to_date are required")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD and SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

trader_addresses = [a.strip() for a in TRADER_ADDRESS.split(",") if a.strip()]

body = {
    "chain": CHAIN,
    "token_address": TOKEN_ADDRESS,
    "date_range": {"from": FROM_DATE, "to": TO_DATE},
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
}
if trader_addresses:
    body["filters"] = {"trader_address": trader_addresses}
if SORT_FIELD:
    body["order_by"] = [{"field": SORT_FIELD, "direction": SORT_DIRECTION}]

response = requests.post(
    "https://api.nansen.ai/api/v1beta1/tgm/historical-pnl-leaderboard",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    # still_holding_balance_ratio crossed with the PnL sign separates conviction from
    # exit behavior: winners who held vs. took profit, losers who held vs. cut losses.
    is_winning = {{__df_name}}["pnl_usd_total"] > 0
    is_holding = {{__df_name}}["still_holding_balance_ratio"] >= 0.5
    {{__df_name}}["conviction_label"] = pd.Series(
        [
            "winning_and_holding" if w and h else
            "winning_but_exited" if w and not h else
            "losing_but_holding" if not w and h else
            "losing_and_exited"
            for w, h in zip(is_winning, is_holding)
        ],
        index={{__df_name}}.index,
    )
    {{__df_name}}["unrealised_share_pct"] = (
        {{__df_name}}["pnl_usd_unrealised"] / {{__df_name}}["pnl_usd_total"].replace(0, pd.NA) * 100
    )
    {{__df_name}} = {{__df_name}}.sort_values("pnl_usd_total", ascending=False, na_position="last").reset_index(drop=True)

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.head(25),
        x="trader_address",
        y="pnl_usd_total",
        color="conviction_label",
        title="Top traders by historical PnL (USD)",
    )
    fig.show()

{{__df_name}}
