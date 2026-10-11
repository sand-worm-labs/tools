# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

ADDRESS = "{{address}}".strip()
CHAIN = "{{chain}}"
AS_OF_DATE = "{{as_of_date}}".strip()
PER_PAGE = "{{per_page}}".strip()

ALLOWED_CHAINS = {"base", "bnb", "ethereum", "solana"}

if not ADDRESS:
    raise ValueError("address is required")
if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not AS_OF_DATE:
    raise ValueError("as_of_date is required")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 20):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")

body = {
    "address": ADDRESS,
    "chain": CHAIN,
    "as_of_date": AS_OF_DATE,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
}

response = requests.post(
    "https://api.nansen.ai/api/v1beta1/profiler/address/historical-transactions",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    # Neither raw array alone says what kind of transaction this was; comparing
    # whether tokens moved in, out, or both turns the two arrays into one read.
    num_received = {{__df_name}}["tokens_received"].apply(lambda t: len(t) if isinstance(t, list) else 0)
    num_sent = {{__df_name}}["tokens_sent"].apply(lambda t: len(t) if isinstance(t, list) else 0)
    {{__df_name}}["flow_direction"] = pd.Series(
        [
            "two_way_swap" if r > 0 and s > 0 else
            "inbound_only" if r > 0 else
            "outbound_only" if s > 0 else
            "none"
            for r, s in zip(num_received, num_sent)
        ],
        index={{__df_name}}.index,
    )

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.sort_values("block_timestamp"),
        x="block_timestamp",
        y="volume_usd",
        color="flow_direction",
        title="Transaction volume (USD) as of {{as_of_date}}",
    )
    fig.show()

{{__df_name}}
