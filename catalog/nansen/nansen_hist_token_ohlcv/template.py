# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAIN = "{{chain}}"
TOKEN_ADDRESS = "{{token_address}}".strip()
DATE_FROM = "{{date_from}}".strip()
AS_OF_DATE = "{{as_of_date}}".strip()
TIMEFRAME = "{{timeframe}}"

ALLOWED_CHAINS = {"base", "bnb", "ethereum", "hyperliquid", "solana"}
ALLOWED_TIMEFRAMES = {"5m", "15m", "30m", "1h", "4h", "1d", "1w"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")
if not DATE_FROM:
    raise ValueError("date_from is required")
if TIMEFRAME not in ALLOWED_TIMEFRAMES:
    raise ValueError(f"Unsupported timeframe: {TIMEFRAME!r}")

body = {
    "chain": CHAIN,
    "token_address": TOKEN_ADDRESS,
    "date_from": DATE_FROM,
    "timeframe": TIMEFRAME,
}
if AS_OF_DATE:
    body["as_of_date"] = AS_OF_DATE

response = requests.post(
    "https://api.nansen.ai/api/v1beta1/tgm/historical-token-ohlcv",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    {{__df_name}}["cumulative_return_pct"] = ({{__df_name}}["close"] / {{__df_name}}["close"].iloc[0] - 1) * 100
    # Drawdown from the running peak close (not just the window's single max) is the
    # risk side of the same window the return is computed over.
    {{__df_name}}["drawdown_from_peak_pct"] = ({{__df_name}}["close"] / {{__df_name}}["close"].cummax() - 1) * 100

    import plotly.express as px

    fig = px.line({{__df_name}}, x="interval_start", y="cumulative_return_pct", title="Cumulative return since window start (%)")
    fig.show()

{{__df_name}}
