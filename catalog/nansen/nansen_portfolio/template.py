# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

WALLET_ADDRESS = "{{wallet_address}}".strip()

if not WALLET_ADDRESS:
    raise ValueError("wallet_address is required")

body = {"wallet_address": WALLET_ADDRESS}

response = requests.post(
    "https://api.nansen.ai/api/v1/portfolio/defi-holdings",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

# No "data" envelope: the response nests tokens under protocols under a summary object.
payload = response.json()
summary = payload.get("summary", {})
rows = []
for protocol in payload.get("protocols", []):
    for token in protocol.get("tokens") or [{}]:
        rows.append({
            "protocol_name": protocol.get("protocol_name"),
            "chain": protocol.get("chain"),
            "protocol_total_value_usd": protocol.get("total_value_usd"),
            "protocol_total_assets_usd": protocol.get("total_assets_usd"),
            "protocol_total_debts_usd": protocol.get("total_debts_usd"),
            "protocol_total_rewards_usd": protocol.get("total_rewards_usd"),
            "token_address": token.get("address"),
            "token_symbol": token.get("symbol"),
            "token_amount": token.get("amount"),
            "token_value_usd": token.get("value_usd"),
            "position_type": token.get("position_type"),
            "portfolio_total_value_usd": summary.get("total_value_usd"),
            "portfolio_total_assets_usd": summary.get("total_assets_usd"),
            "portfolio_total_debts_usd": summary.get("total_debts_usd"),
            "portfolio_total_rewards_usd": summary.get("total_rewards_usd"),
            "portfolio_token_count": summary.get("token_count"),
            "portfolio_protocol_count": summary.get("protocol_count"),
        })

{{__df_name}} = pd.DataFrame(rows)

# Debts and assets are reported separately; dividing them surfaces leverage
# risk a position-by-position USD listing doesn't show on its own.
if not {{__df_name}}.empty:
    {{__df_name}}["protocol_leverage_pct"] = (
        {{__df_name}}["protocol_total_debts_usd"] / {{__df_name}}["protocol_total_assets_usd"].replace(0, pd.NA) * 100
    )
    {{__df_name}}["leverage_flag"] = {{__df_name}}["protocol_leverage_pct"].apply(
        lambda p: "leveraged" if pd.notna(p) and p > 0 else "unleveraged"
    )
    {{__df_name}} = {{__df_name}}.sort_values("token_value_usd", ascending=False, na_position="last").reset_index(drop=True)

    import plotly.express as px

    protocol_totals = {{__df_name}}.drop_duplicates("protocol_name")
    fig = px.bar(
        protocol_totals.sort_values("protocol_total_value_usd", ascending=False),
        x="protocol_name",
        y="protocol_total_value_usd",
        color="leverage_flag",
        title="DeFi value by protocol (USD)",
    )
    fig.show()

{{__df_name}}
