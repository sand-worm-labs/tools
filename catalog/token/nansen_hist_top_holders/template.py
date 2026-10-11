# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAIN = "{{chain}}"
TOKEN_ADDRESS = "{{token_address}}".strip()
AS_OF_DATE = "{{as_of_date}}".strip()
LABEL_TYPE = "{{label_type}}".strip()
INCLUDE_SM_LABELS = "{{include_sm_labels}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}".strip()
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {"base", "bnb", "ethereum", "solana"}
ALLOWED_LABEL_TYPES = {"all_holders", "whale", "public_figure", "exchange", "smart_money"}
ALLOWED_SM_LABELS = {
    "30D Smart Trader", "90D Smart Trader", "180D Smart Trader", "Fund", "Smart Trader",
    "Smart Dex Trader", "30D Smart Dex Trader", "90D Smart Dex Trader",
    "180D Smart Dex Trader", "Public Figure", "Exchange", "Whale", "BananaGun Bot User",
    "Top Maestro Bot User", "Top BananaGun Bot User", "Maestro Bot User",
    "Early MAGIC Miner", "First Mover LP", "First Mover Staking", "Profitable LP",
    "Smart HL Perps Trader",
}
ALLOWED_SORT_FIELDS = {
    "token_amount", "value_usd", "total_outflow", "total_inflow", "balance_change_24h",
    "balance_change_7d", "balance_change_30d", "ownership_percentage",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")
if not AS_OF_DATE:
    raise ValueError("as_of_date is required")
if LABEL_TYPE and LABEL_TYPE not in ALLOWED_LABEL_TYPES:
    raise ValueError(f"Unsupported label_type: {LABEL_TYPE!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD and SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

sm_labels = [label.strip() for label in INCLUDE_SM_LABELS.split(",") if label.strip()]
for label in sm_labels:
    if label not in ALLOWED_SM_LABELS:
        raise ValueError(f"Unsupported smart money label: {label!r}")

body = {
    "chain": CHAIN,
    "token_address": TOKEN_ADDRESS,
    "as_of_date": AS_OF_DATE,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
}
if LABEL_TYPE:
    body["label_type"] = LABEL_TYPE
if sm_labels:
    body["filters"] = {"include_sm_labels": sm_labels}
if SORT_FIELD:
    body["order_by"] = [{"field": SORT_FIELD, "direction": SORT_DIRECTION}]

response = requests.post(
    "https://api.nansen.ai/api/v1beta1/tgm/historical-top-holders",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    # Cross-timeframe sign agreement on balance_change_* turns three snapshots into one
    # read: still adding at every horizon vs. still cutting vs. having just turned.
    def _trend(row):
        h24, d7, d30 = row["balance_change_24h"], row["balance_change_7d"], row["balance_change_30d"]
        if h24 > 0 and d7 > 0 and d30 > 0:
            return "sustained_accumulation"
        if h24 < 0 and d7 < 0 and d30 < 0:
            return "sustained_distribution"
        if h24 > 0 and d7 < 0:
            return "reversing_to_buy"
        if h24 < 0 and d7 > 0:
            return "reversing_to_sell"
        return "mixed"

    {{__df_name}}["holder_trend"] = {{__df_name}}.apply(_trend, axis=1)
    {{__df_name}}["entrenched_whale"] = (
        ({{__df_name}}["ownership_percentage"] >= {{__df_name}}["ownership_percentage"].quantile(0.9))
        & ({{__df_name}}["holder_trend"] == "sustained_accumulation")
    )
    {{__df_name}} = {{__df_name}}.sort_values("ownership_percentage", ascending=False, na_position="last").reset_index(drop=True)

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.head(25),
        x="address",
        y="ownership_percentage",
        color="holder_trend",
        title="Top holder concentration (ownership %) as of {{as_of_date}}",
    )
    fig.show()

{{__df_name}}
