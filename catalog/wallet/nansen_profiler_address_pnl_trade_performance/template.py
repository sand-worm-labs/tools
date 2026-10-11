# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

ADDRESS = "{{address}}".strip()
ENTITY_NAME = "{{entity_name}}".strip()
CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()
SHOW_REALIZED = "{{show_realized}}".strip().lower()
TOKEN_ADDRESS = "{{token_address}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "all", "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "linea",
    "mantle", "monad", "optimism", "plasma", "polygon", "robinhood", "sei",
    "solana", "sonic", "sui",
}
ALLOWED_SORT_FIELDS = {
    "pnl_usd_realised", "roi_percent_realised", "pnl_usd_unrealised",
    "roi_percent_unrealised", "bought_usd", "sold_usd", "holding_usd",
}

if not ADDRESS and not ENTITY_NAME:
    raise ValueError("Either address or entity_name is required")
if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if SHOW_REALIZED not in {"true", "false"}:
    raise ValueError(f"Invalid show_realized: {SHOW_REALIZED!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

filters = {"show_realized": SHOW_REALIZED == "true"}
if TOKEN_ADDRESS:
    filters["token_address"] = TOKEN_ADDRESS

body = {
    "chain": CHAIN,
    "filters": filters,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if ADDRESS:
    body["address"] = ADDRESS
if ENTITY_NAME:
    body["entity_name"] = ENTITY_NAME
if DATE_FROM and DATE_TO:
    body["date"] = {"from": DATE_FROM, "to": DATE_TO}

response = requests.post(
    "https://api.nansen.ai/api/v1/profiler/address/pnl",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

# A big PnL in raw dollars can just mean a big position, not a good trade —
# sizing the combined (realized + unrealized) PnL against the capital
# actually put in (cost basis) is the read that tells winners from whales.
if not {{__df_name}}.empty:
    {{__df_name}}["total_pnl_usd"] = (
        {{__df_name}}["pnl_usd_realised"].fillna(0) + {{__df_name}}["pnl_usd_unrealised"].fillna(0)
    )
    {{__df_name}}["total_roi_pct"] = (
        {{__df_name}}["total_pnl_usd"] / {{__df_name}}["cost_basis_usd"].replace(0, pd.NA) * 100
    )

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.head(15),
        x="token_symbol",
        y="total_roi_pct",
        color="total_pnl_usd",
        title="Token ROI on capital deployed (realized + unrealized)",
    )
    fig.show()

{{__df_name}}
