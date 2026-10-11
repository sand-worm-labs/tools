# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

AS_OF_DATE = "{{as_of_date}}".strip()
CHAINS = "{{chains}}".strip()
SM_FILTER = "{{sm_filter}}".strip()
PER_PAGE = "{{per_page}}".strip()

ALLOWED_CHAINS = {
    "all", "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "hyperevm",
    "iotaevm", "linea", "mantle", "monad", "optimism", "plasma", "polygon",
    "robinhood", "sei", "solana", "sonic",
}
ALLOWED_SM_LABELS = {
    "Fund", "Smart Trader", "30D Smart Trader", "90D Smart Trader", "180D Smart Trader",
    "Smart Dex Trader", "30D Smart Dex Trader", "90D Smart Dex Trader",
    "180D Smart Dex Trader", "Smart HL Perps Trader",
}

if not AS_OF_DATE:
    raise ValueError("as_of_date is required")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")

chains = [c.strip() for c in CHAINS.split(",") if c.strip()]
for c in chains:
    if c not in ALLOWED_CHAINS:
        raise ValueError(f"Unsupported chain: {c!r}")

sm_labels = [label.strip() for label in SM_FILTER.split(",") if label.strip()]
for label in sm_labels:
    if label not in ALLOWED_SM_LABELS:
        raise ValueError(f"Unsupported smart money label: {label!r}")

body = {
    "as_of_date": AS_OF_DATE,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
}
if chains:
    body["chains"] = chains
if sm_labels:
    body["filters"] = {"sm_filter": sm_labels}

response = requests.post(
    "https://api.nansen.ai/api/v1beta1/smart-money/historical-token-balances",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    # Direction alone (24h change) doesn't say whether it's a broad consensus move or
    # one whale; crossing it with holder breadth does.
    median_holders = {{__df_name}}["holders_count"].median()
    change = {{__df_name}}["balance_24h_percent_change"]
    broad = {{__df_name}}["holders_count"] >= median_holders
    {{__df_name}}["accumulation_breadth"] = pd.Series(
        [
            "broad_accumulation" if c > 0 and b else
            "concentrated_accumulation" if c > 0 and not b else
            "broad_distribution" if c < 0 and b else
            "concentrated_distribution" if c < 0 and not b else
            "flat"
            for c, b in zip(change, broad)
        ],
        index={{__df_name}}.index,
    )
    {{__df_name}} = {{__df_name}}.sort_values("value_usd", ascending=False, na_position="last").reset_index(drop=True)

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.head(25),
        x="token_symbol",
        y="value_usd",
        color="accumulation_breadth",
        title="Smart money token holdings as of {{as_of_date}}",
    )
    fig.show()

{{__df_name}}
