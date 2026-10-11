# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

TOKEN_SYMBOL = "{{token_symbol}}".strip()
FROM_DATE = "{{from_date}}".strip()
TO_DATE = "{{to_date}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"
MIN_REALISED_PNL_USD = "{{min_realised_pnl_usd}}".strip()

ALLOWED_SORT_FIELDS = {
    "pnl_usd_realised", "pnl_usd_unrealised", "pnl_usd_total", "roi_percent_total",
    "roi_percent_realised", "roi_percent_unrealised", "holding_amount",
    "position_value_usd", "max_balance_held", "max_balance_held_usd",
    "still_holding_balance_ratio", "netflow_amount_usd", "netflow_amount", "nof_trades",
}

if not TOKEN_SYMBOL:
    raise ValueError("token_symbol is required")
if not FROM_DATE:
    raise ValueError("from_date is required")
if not TO_DATE:
    raise ValueError("to_date is required")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

filters = {}
if MIN_REALISED_PNL_USD:
    filters["pnl_usd_realised"] = {"min": float(MIN_REALISED_PNL_USD)}

body = {
    "token_symbol": TOKEN_SYMBOL,
    "date": {"from": FROM_DATE, "to": TO_DATE},
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if filters:
    body["filters"] = filters

response = requests.post(
    "https://api.nansen.ai/api/v1/tgm/perp-pnl-leaderboard",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    # Size-adjusted skill read: PnL per trade, not just total PnL.
    {{__df_name}}["pnl_per_trade_usd"] = {{__df_name}}["pnl_usd_total"] / {{__df_name}}["nof_trades"].replace(0, pd.NA)
    # Mismatch flag: a huge PnL-per-trade built on a handful of fills looks like
    # one lucky trade, not sustained skill — total PnL and trade count alone
    # don't surface that, only comparing them does.
    median_abs_pnl_per_trade = {{__df_name}}["pnl_per_trade_usd"].abs().median()
    {{__df_name}}["thin_sample_flag"] = ({{__df_name}}["nof_trades"] <= 3) & (
        {{__df_name}}["pnl_per_trade_usd"].abs() > 3 * median_abs_pnl_per_trade
    )

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.sort_values("pnl_usd_total", ascending=False).head(25),
        x="trader_address",
        y="pnl_usd_total",
        color="thin_sample_flag",
        title=f"Top {TOKEN_SYMBOL} perp PnL leaderboard",
    )
    fig.show()

{{__df_name}}
