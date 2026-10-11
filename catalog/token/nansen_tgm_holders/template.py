# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAIN = "{{chain}}".strip()
TOKEN_ADDRESS = "{{token_address}}".strip()
LABEL_TYPE = "{{label_type}}"
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "arbitrum", "arc", "avalanche", "base", "bitcoin", "bnb", "ethereum",
    "hyperevm", "injective", "iotaevm", "linea", "mantle", "mantra", "monad",
    "near", "optimism", "plasma", "polygon", "robinhood", "sei", "solana",
    "sonic", "starknet", "sui", "ton", "tron",
}
ALLOWED_LABEL_TYPES = {"whale", "public_figure", "smart_money", "all_holders", "exchange"}
ALLOWED_SORT_FIELDS = {
    "address", "name", "token_amount", "total_outflow", "total_inflow",
    "balance_change_24h", "balance_change_7d", "balance_change_30d",
    "ownership_percentage", "value_usd",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")
if LABEL_TYPE not in ALLOWED_LABEL_TYPES:
    raise ValueError(f"Unsupported label_type: {LABEL_TYPE!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

body = {
    "chain": CHAIN,
    "token_address": TOKEN_ADDRESS,
    "label_type": LABEL_TYPE,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}

response = requests.post(
    "https://api.nansen.ai/api/v1/tgm/holders",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    # Ownership % alone doesn't say whether a big holder is adding or exiting, and
    # a $ balance change alone doesn't say how large relative to their own stack.
    # Combining them finds "big and moving" holders a plain holder list hides.
    {{__df_name}}["balance_change_30d_pct_of_position"] = (
        {{__df_name}}["balance_change_30d"] / {{__df_name}}["token_amount"].replace(0, pd.NA) * 100
    )
    size_cutoff = {{__df_name}}["ownership_percentage"].quantile(0.75)
    {{__df_name}}["whale_conviction"] = {{__df_name}}.apply(
        lambda r: (
            "large_accumulator" if r["ownership_percentage"] >= size_cutoff and r["balance_change_30d"] > 0
            else "large_distributor" if r["ownership_percentage"] >= size_cutoff and r["balance_change_30d"] < 0
            else "n/a"
        ),
        axis=1,
    )

    import plotly.express as px

    fig = px.scatter(
        {{__df_name}}, x="ownership_percentage", y="balance_change_30d_pct_of_position",
        color="whale_conviction", hover_name="address",
        title=f"Holder size vs 30d position change — {TOKEN_ADDRESS}",
    )
    fig.show()

{{__df_name}}
