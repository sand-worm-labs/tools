# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

ADDRESS = "{{address}}".strip()
AS_OF_DATE = "{{as_of_date}}".strip()
CHAIN = "{{chain}}"
PER_PAGE = "{{per_page}}".strip()

ALLOWED_CHAINS = {"all", "base", "bnb", "ethereum", "mantra", "solana"}

if not ADDRESS:
    raise ValueError("address is required")
if not AS_OF_DATE:
    raise ValueError("as_of_date is required")
if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")

body = {
    "address": ADDRESS,
    "as_of_date": AS_OF_DATE,
    "chain": CHAIN,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
}

response = requests.post(
    "https://api.nansen.ai/api/v1beta1/profiler/address/historical-token-balances",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    # No single holding's value_usd says anything about risk on its own; weighed
    # against the wallet's total it becomes a concentration read.
    total_value_usd = {{__df_name}}["value_usd"].sum()
    {{__df_name}}["pct_of_portfolio"] = {{__df_name}}["value_usd"] / total_value_usd * 100 if total_value_usd else 0
    {{__df_name}}["concentrated_portfolio"] = bool(({{__df_name}}["pct_of_portfolio"] >= 50).any())
    {{__df_name}} = {{__df_name}}.sort_values("value_usd", ascending=False, na_position="last").reset_index(drop=True)

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.head(15),
        x="token_symbol",
        y="pct_of_portfolio",
        title="Portfolio composition as of {{as_of_date}} (% of total value)",
    )
    fig.show()

{{__df_name}}
