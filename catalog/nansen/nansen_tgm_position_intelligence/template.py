# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

TOKEN_ADDRESS = "{{token_address}}".strip()

if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")

body = {"token_address": TOKEN_ADDRESS}

response = requests.post(
    "https://api.nansen.ai/api/v1/tgm/position-intelligence",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

COHORTS = ["smart_trader", "whale", "public_figure"]

if not {{__df_name}}.empty:
    for cohort in COHORTS:
        longs = {{__df_name}}[f"{cohort}_longs_usd"]
        shorts = {{__df_name}}[f"{cohort}_shorts_usd"]
        total = {{__df_name}}[f"{cohort}_total_usd"].replace(0, pd.NA)
        {{__df_name}}[f"{cohort}_skew"] = (longs - shorts) / total

    # Each cohort's own long/short tilt is in the dashboard already; whether the
    # "smart" cohort is positioned against the whale cohort is not — that split
    # is the actual trade signal (who's likely right).
    {{__df_name}}["smart_vs_whale_divergence"] = (
        ({{__df_name}}["smart_trader_skew"] > 0) != ({{__df_name}}["whale_skew"] > 0)
    )

    import plotly.express as px

    melted = {{__df_name}}[[f"{c}_longs_usd" for c in COHORTS] + [f"{c}_shorts_usd" for c in COHORTS]].melt(
        var_name="field", value_name="usd"
    )
    melted["cohort"] = melted["field"].str.replace("_longs_usd", "", regex=False).str.replace("_shorts_usd", "", regex=False)
    melted["side"] = melted["field"].apply(lambda f: "long" if "longs" in f else "short")
    fig = px.bar(
        melted, x="cohort", y="usd", color="side", barmode="group",
        title=f"Long/short exposure by cohort — {TOKEN_ADDRESS}",
    )
    fig.show()

{{__df_name}}
