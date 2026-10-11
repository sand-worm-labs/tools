# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()
CHAINS = "{{chains}}"
TOKEN_ADDRESS = "{{token_address}}".strip()
INCLUDE_LABELS = "{{include_smart_money_labels}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {"arc", "base", "bnb", "ethereum", "monad", "robinhood", "solana"}
ALLOWED_LABELS = {
    "Fund", "Smart Trader", "30D Smart Trader", "90D Smart Trader", "180D Smart Trader",
    "Smart Dex Trader", "30D Smart Dex Trader", "90D Smart Dex Trader", "180D Smart Dex Trader",
    "Smart HL Perps Trader",
}

if not DATE_FROM:
    raise ValueError("date_from is required")
chains = [c.strip() for c in CHAINS.split(",") if c.strip()]
if not chains:
    raise ValueError("chains is required")
for c in chains:
    if c not in ALLOWED_CHAINS:
        raise ValueError(f"Unsupported chain: {c!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

labels = [label.strip() for label in INCLUDE_LABELS.split(",") if label.strip()]
for label in labels:
    if label not in ALLOWED_LABELS:
        raise ValueError(f"Unsupported smart money label: {label!r}")

date_range = {"from": DATE_FROM}
if DATE_TO:
    date_range["to"] = DATE_TO

filters = {}
if TOKEN_ADDRESS:
    filters["token_address"] = TOKEN_ADDRESS
if labels:
    filters["include_smart_money_labels"] = labels

body = {
    "date_range": date_range,
    "chains": chains,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": "date", "direction": SORT_DIRECTION}],
}
if filters:
    body["filters"] = filters

response = requests.post(
    "https://api.nansen.ai/api/v1/smart-money/historical-holdings",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

# value_usd_per_holder sizes the position by conviction (few whales vs
# broad). holding_trend catches a divergence the raw rows don't surface on
# their own: the position's direction over the whole window vs. its most
# recent 24h move — e.g. a long build-up that just started unwinding.
if not {{__df_name}}.empty:
    {{__df_name}}["value_usd_per_holder"] = (
        {{__df_name}}["value_usd"] / {{__df_name}}["holders_count"].replace(0, pd.NA)
    )

    ordered = {{__df_name}}.sort_values(["token_address", "chain", "date"])
    range_change = ordered.groupby(["token_address", "chain"])["value_usd"].transform(
        lambda s: s.iloc[-1] - s.iloc[0]
    )
    {{__df_name}}.loc[ordered.index, "_range_change"] = range_change

    def _trend(row):
        short, long = row.get("balance_24h_percent_change"), row.get("_range_change")
        if pd.isna(short) or pd.isna(long):
            return "unknown"
        if short > 0 and long > 0:
            return "sustained_accumulation"
        if short < 0 and long < 0:
            return "sustained_distribution"
        if short < 0 and long > 0:
            return "reversing_to_sell"
        if short > 0 and long < 0:
            return "reversing_to_buy"
        return "mixed"

    {{__df_name}}["holding_trend"] = {{__df_name}}.apply(_trend, axis=1)
    {{__df_name}} = {{__df_name}}.drop(columns="_range_change").sort_values("date", ascending=False).reset_index(drop=True)

    import plotly.express as px

    fig = px.line(
        {{__df_name}}.sort_values("date"),
        x="date",
        y="value_usd",
        color="token_symbol",
        title="Smart money historical holdings value (USD)",
    )
    fig.show()

{{__df_name}}
