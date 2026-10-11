# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAIN = "{{chain}}"
TOKEN_ADDRESS = "{{token_address}}".strip()
FROM_DATE = "{{from_date}}".strip()
TO_DATE = "{{to_date}}".strip()

ALLOWED_CHAINS = {"base", "bnb", "ethereum", "solana"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")
if not FROM_DATE or not TO_DATE:
    raise ValueError("from_date and to_date are required")

body = {
    "chain": CHAIN,
    "token_address": TOKEN_ADDRESS,
    "date_range": {"from": FROM_DATE, "to": TO_DATE},
}

response = requests.post(
    "https://api.nansen.ai/api/v1beta1/tgm/historical-token-flow-summary",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    flow_cols = [
        "public_figure_net_flow_usd", "top_pnl_net_flow_usd", "whale_net_flow_usd",
        "exchange_net_flow_usd", "smart_trader_net_flow_usd", "fresh_wallets_net_flow_usd",
    ]
    {{__df_name}}["dominant_segment"] = {{__df_name}}[flow_cols].abs().idxmax(axis=1).str.replace("_net_flow_usd", "", regex=False)
    # Smart money buying while exchange-directed flow (often a precursor to selling) is
    # muted is a bullish divergence; the reverse is bearish. Neither segment alone shows this.
    {{__df_name}}["smart_vs_exchange_divergence_usd"] = (
        {{__df_name}}["smart_trader_net_flow_usd"] - {{__df_name}}["exchange_net_flow_usd"]
    )

    import plotly.express as px

    segment_flows = {{__df_name}}.melt(
        id_vars=["token_symbol"], value_vars=flow_cols, var_name="segment", value_name="net_flow_usd"
    )
    fig = px.bar(segment_flows, x="segment", y="net_flow_usd", color="token_symbol", title="Historical net flow by segment (USD)")
    fig.show()

{{__df_name}}
