# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAIN = "{{chain}}".strip()
TOKEN_ADDRESS = "{{token_address}}".strip()
TIMEFRAME = "{{timeframe}}"

ALLOWED_CHAINS = {
    "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "hyperevm",
    "injective", "linea", "mantle", "mantra", "monad", "near", "optimism",
    "plasma", "polygon", "robinhood", "sei", "solana", "sonic", "starknet",
    "sui", "ton", "tron",
}
ALLOWED_TIMEFRAMES = {"5m", "1h", "6h", "12h", "1d", "7d"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")
if TIMEFRAME not in ALLOWED_TIMEFRAMES:
    raise ValueError(f"Unsupported timeframe: {TIMEFRAME!r}")

body = {
    "chain": CHAIN,
    "token_address": TOKEN_ADDRESS,
    "timeframe": TIMEFRAME,
}

response = requests.post(
    "https://api.nansen.ai/api/v1/tgm/flow-intelligence",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

SEGMENTS = ["public_figure", "top_pnl", "whale", "smart_trader", "exchange", "fresh_wallets"]
FLOW_COLS = [f"{s}_net_flow_usd" for s in SEGMENTS]

if not {{__df_name}}.empty:
    {{__df_name}}.insert(0, "chain", CHAIN)
    {{__df_name}}.insert(1, "token_address", TOKEN_ADDRESS)
    {{__df_name}}.insert(2, "timeframe", TIMEFRAME)

    {{__df_name}}["total_net_flow_usd"] = {{__df_name}}[FLOW_COLS].sum(axis=1, skipna=True)
    {{__df_name}}["dominant_segment"] = (
        {{__df_name}}[FLOW_COLS].abs().idxmax(axis=1).str.replace("_net_flow_usd", "", regex=False)
    )

    import plotly.express as px

    melted = {{__df_name}}[FLOW_COLS].melt(var_name="segment", value_name="net_flow_usd")
    melted["segment"] = melted["segment"].str.replace("_net_flow_usd", "", regex=False)
    fig = px.bar(melted, x="segment", y="net_flow_usd", title=f"Flow intelligence by segment ({TIMEFRAME})")
    fig.show()

{{__df_name}}
