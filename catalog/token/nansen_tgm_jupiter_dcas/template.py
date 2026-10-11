# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

TOKEN_ADDRESS = "{{token_address}}".strip()
STATUS = "{{status}}".strip()
INCLUDE_LABELS = "{{include_smart_money_labels}}".strip()
PER_PAGE = "{{per_page}}".strip()

ALLOWED_LABELS = {
    "30D Smart Trader", "90D Smart Trader", "180D Smart Trader", "Fund",
    "Smart Trader", "Public Figure", "Exchange", "Whale", "BananaGun Bot User",
    "Top Maestro Bot User", "Top BananaGun Bot User", "Maestro Bot User",
    "Early MAGIC Miner", "First Mover LP", "First Mover Staking",
    "Profitable LP", "Smart HL Perps Trader",
}

if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")
if STATUS and STATUS not in {"Active", "Closed"}:
    raise ValueError(f"Unsupported status: {STATUS!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")

labels = [label.strip() for label in INCLUDE_LABELS.split(",") if label.strip()]
for label in labels:
    if label not in ALLOWED_LABELS:
        raise ValueError(f"Unsupported smart money label: {label!r}")

filters = {}
if STATUS:
    filters["status"] = STATUS
if labels:
    filters["include_smart_money_labels"] = labels

body = {
    "token_address": TOKEN_ADDRESS,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
}
if filters:
    body["filters"] = filters

response = requests.post(
    "https://api.nansen.ai/api/v1/tgm/jup-dca",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    {{__df_name}}["dca_completion_pct"] = (
        {{__df_name}}["deposit_spent"] / {{__df_name}}["deposit_amount"].replace(0, pd.NA) * 100
    )
    {{__df_name}}["nearing_completion_flag"] = (
        ({{__df_name}}["status"] == "Active") & ({{__df_name}}["dca_completion_pct"] >= 90)
    )

    active = {{__df_name}}[{{__df_name}}["status"] == "Active"]
    if not active.empty:
        import plotly.express as px

        fig = px.histogram(
            active, x="dca_completion_pct",
            title=f"Active Jupiter DCA completion — remaining pipeline for {TOKEN_ADDRESS}",
        )
        fig.show()

{{__df_name}}
