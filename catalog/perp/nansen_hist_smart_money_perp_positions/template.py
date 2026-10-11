# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

COIN = "{{coin}}".strip()
AS_OF_DATE = "{{as_of_date}}".strip()
SM_LABEL_FILTER = "{{sm_label_filter}}".strip()

ALLOWED_SM_LABELS = {
    "Fund", "Smart Trader", "30D Smart Trader", "90D Smart Trader", "180D Smart Trader",
    "Smart Dex Trader", "30D Smart Dex Trader", "90D Smart Dex Trader",
    "180D Smart Dex Trader", "Smart HL Perps Trader",
}

if not COIN:
    raise ValueError("coin is required")
if not AS_OF_DATE:
    raise ValueError("as_of_date is required")

sm_labels = [label.strip() for label in SM_LABEL_FILTER.split(",") if label.strip()]
for label in sm_labels:
    if label not in ALLOWED_SM_LABELS:
        raise ValueError(f"Unsupported smart money label: {label!r}")

body = {
    "coin": COIN,
    "as_of_date": AS_OF_DATE,
}
if sm_labels:
    body["sm_label_filter"] = sm_labels

response = requests.post(
    "https://api.nansen.ai/api/v1beta1/tgm/historical-token-recent-flows-summary-perps",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    # Long/short exposure alone doesn't say whether cohorts agree; netting each cohort
    # and comparing nets across cohorts is where positioning divergence shows up.
    {{__df_name}}["smart_trader_net_usd"] = {{__df_name}}["smart_trader_longs_usd"] - {{__df_name}}["smart_trader_shorts_usd"]
    {{__df_name}}["whale_net_usd"] = {{__df_name}}["whale_longs_usd"] - {{__df_name}}["whale_shorts_usd"]
    smart_long = {{__df_name}}["smart_trader_net_usd"] > 0
    whale_long = {{__df_name}}["whale_net_usd"] > 0
    {{__df_name}}["smart_vs_whale_positioning"] = pd.Series(
        [
            "aligned_long" if s and w else
            "aligned_short" if not s and not w else
            "smart_long_whale_short" if s and not w else
            "smart_short_whale_long"
            for s, w in zip(smart_long, whale_long)
        ],
        index={{__df_name}}.index,
    )

    import plotly.express as px

    net_cols = ["smart_trader_net_usd", "whale_net_usd"]
    net_exposure = {{__df_name}}.melt(id_vars=["coin"], value_vars=net_cols, var_name="cohort", value_name="net_usd")
    fig = px.bar(net_exposure, x="cohort", y="net_usd", color="coin", title="Net perp exposure by cohort (USD) as of {{as_of_date}}")
    fig.show()

{{__df_name}}
