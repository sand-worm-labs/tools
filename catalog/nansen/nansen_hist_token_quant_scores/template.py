# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAIN = "{{chain}}"
TOKEN_ADDRESS = "{{token_address}}".strip()
AS_OF_DATE = "{{as_of_date}}".strip()

ALLOWED_CHAINS = {
    "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "hyperevm", "hyperliquid",
    "injective", "iotaevm", "linea", "mantle", "mantra", "monad", "near", "optimism",
    "plasma", "polygon", "robinhood", "sei", "solana", "sonic", "starknet", "sui",
    "ton", "tron",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")
if not AS_OF_DATE:
    raise ValueError("as_of_date is required")

body = {
    "chain": CHAIN,
    "token_address": TOKEN_ADDRESS,
    "as_of_date": AS_OF_DATE,
}

response = requests.post(
    "https://api.nansen.ai/api/v1beta1/tgm/historical-token-quant-scores",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    # A single indicator's percentile restates itself; the mismatch only shows up when
    # reward-side and risk-side indicators are compared against each other.
    reward_avg = {{__df_name}}.loc[{{__df_name}}["model_type"] == "reward", "signal_percentile"].mean()
    risk_avg = {{__df_name}}.loc[{{__df_name}}["model_type"] == "risk", "signal_percentile"].mean()
    {{__df_name}}["risk_reward_mismatch"] = bool(pd.notna(reward_avg) and pd.notna(risk_avg) and reward_avg >= 70 and risk_avg >= 70)
    {{__df_name}} = {{__df_name}}.sort_values("signal_percentile", ascending=False, na_position="last").reset_index(drop=True)

    import plotly.express as px

    fig = px.bar(
        {{__df_name}},
        x="indicator_type",
        y="signal_percentile",
        color="model_type",
        title="Quant score indicator percentiles as of {{as_of_date}}",
    )
    fig.show()

{{__df_name}}
