# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAINS = "{{chains}}"
TOKEN_ADDRESS = "{{token_address}}".strip()
MIN_VALUE_USD = "{{min_value_usd}}".strip()
INCLUDE_STABLECOINS = "{{include_stablecoins}}"
INCLUDE_NATIVE_TOKENS = "{{include_native_tokens}}"
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "all", "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "hyperevm",
    "iotaevm", "linea", "mantle", "monad", "optimism", "plasma", "polygon",
    "robinhood", "sei", "solana", "sonic",
}
ALLOWED_SORT_FIELDS = {
    "chain", "token_address", "token_symbol", "value_usd", "balance_24h_percent_change",
    "holders_count", "share_of_holdings_percent", "token_age_days", "market_cap_usd",
}

chains = [c.strip() for c in CHAINS.split(",") if c.strip()]
if not chains:
    raise ValueError("chains is required")
for c in chains:
    if c not in ALLOWED_CHAINS:
        raise ValueError(f"Unsupported chain: {c!r}")
if MIN_VALUE_USD and not MIN_VALUE_USD.replace(".", "", 1).isdigit():
    raise ValueError(f"Invalid min_value_usd: {MIN_VALUE_USD!r}")
if INCLUDE_STABLECOINS not in {"true", "false"}:
    raise ValueError(f"Invalid include_stablecoins: {INCLUDE_STABLECOINS!r}")
if INCLUDE_NATIVE_TOKENS not in {"true", "false"}:
    raise ValueError(f"Invalid include_native_tokens: {INCLUDE_NATIVE_TOKENS!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

filters = {
    "include_stablecoins": INCLUDE_STABLECOINS == "true",
    "include_native_tokens": INCLUDE_NATIVE_TOKENS == "true",
}
if TOKEN_ADDRESS:
    filters["token_address"] = TOKEN_ADDRESS
if MIN_VALUE_USD:
    filters["value_usd"] = {"min": float(MIN_VALUE_USD)}

body = {
    "chains": chains,
    "filters": filters,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}

response = requests.post(
    "https://api.nansen.ai/api/v1beta1/funds/holdings",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

# value_usd_per_holder sizes the position by how many funds share it;
# fund_signal combines that with share_of_holdings_percent — a large share
# held by a handful of funds reads very differently from the same share
# spread across many, which neither field says alone.
if not {{__df_name}}.empty:
    {{__df_name}}["value_usd_per_holder"] = (
        {{__df_name}}["value_usd"] / {{__df_name}}["holders_count"].replace(0, pd.NA)
    )
    median_holders = {{__df_name}}["holders_count"].median()

    def _signal(row):
        share, holders = row.get("share_of_holdings_percent"), row.get("holders_count")
        if pd.isna(share) or pd.isna(holders):
            return "unknown"
        if share < 5:
            return "minor_position"
        return "concentrated_conviction" if holders < median_holders else "broad_consensus"

    {{__df_name}}["fund_signal"] = {{__df_name}}.apply(_signal, axis=1)
    {{__df_name}} = {{__df_name}}.sort_values("value_usd", ascending=False, na_position="last").reset_index(drop=True)

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.head(25),
        x="token_symbol",
        y="value_usd",
        color="fund_signal",
        title="Fund holdings by value (USD)",
    )
    fig.show()

{{__df_name}}
