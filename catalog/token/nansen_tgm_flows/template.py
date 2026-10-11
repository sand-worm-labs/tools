# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAIN = "{{chain}}".strip()
TOKEN_ADDRESS = "{{token_address}}".strip()
DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()
LABEL = "{{label}}"
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "hyperevm",
    "hyperliquid", "injective", "iotaevm", "linea", "mantle", "mantra", "monad",
    "near", "optimism", "plasma", "polygon", "robinhood", "sei", "solana",
    "sonic", "starknet", "sui", "ton", "tron",
}
ALLOWED_LABELS = {"whale", "public_figure", "smart_money", "top_100_holders", "exchange"}
ALLOWED_SORT_FIELDS = {
    "date", "price_usd", "token_amount", "value_usd", "holders_count",
    "total_inflows_count", "total_outflows_count", "total_inflows_dex",
    "total_outflows_dex", "total_inflows_cex", "total_outflows_cex",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")
if not DATE_FROM or not DATE_TO:
    raise ValueError("date_from and date_to are required")
if LABEL not in ALLOWED_LABELS:
    raise ValueError(f"Unsupported label: {LABEL!r}")
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
    "label": LABEL,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}

response = requests.post(
    "https://api.nansen.ai/api/v1/tgm/flows",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    {{__df_name}} = {{__df_name}}.sort_values("date").reset_index(drop=True)
    price_change = {{__df_name}}["price_usd"].diff()
    holders_change = {{__df_name}}["holders_count"].diff()

    # Price alone or holder count alone each miss the other side of the story —
    # more holders while price falls is accumulation into weakness, not visible
    # from either series on its own.
    {{__df_name}}["holders_count_change"] = holders_change
    {{__df_name}}["price_vs_holders_signal"] = [
        "accumulation_divergence" if p < 0 and h > 0
        else "distribution_divergence" if p > 0 and h < 0
        else "aligned"
        for p, h in zip(price_change.fillna(0), holders_change.fillna(0))
    ]

    import plotly.express as px

    fig = px.line(
        {{__df_name}}, x="date", y="value_usd",
        title=f"{LABEL} cohort value held — {TOKEN_ADDRESS}",
    )
    fig.show()

{{__df_name}}
