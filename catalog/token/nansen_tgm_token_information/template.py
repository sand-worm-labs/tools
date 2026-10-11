# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests
from html import escape
from sandworm_theme import card, note, show, use_theme

use_theme()

CHAIN = "{{chain}}".strip()
TOKEN_ADDRESS = "{{token_address}}".strip()
TIMEFRAME = "{{timeframe}}"

ALLOWED_CHAINS = {
    "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "hyperevm",
    "hyperliquid", "injective", "iotaevm", "linea", "mantle", "mantra", "monad",
    "near", "optimism", "plasma", "polygon", "robinhood", "sei", "solana",
    "sonic", "starknet", "sui", "ton", "tron",
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
    "https://api.nansen.ai/api/v1/tgm/token-information",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

data = response.json().get("data", {}) or {}
token_details = data.get("token_details", {}) or {}
spot_metrics = data.get("spot_metrics", {}) or {}
row = {
    "name": data.get("name"),
    "symbol": data.get("symbol"),
    "contract_address": data.get("contract_address"),
    "logo": data.get("logo"),
    **token_details,
    **spot_metrics,
}

{{__df_name}} = pd.DataFrame([row]) if data else pd.DataFrame()

if not {{__df_name}}.empty:
    df = {{__df_name}}
    for col in ("market_cap_usd", "volume_total_usd", "buy_volume_usd", "sell_volume_usd", "total_buys",
                "total_sells", "unique_buyers", "unique_sellers", "liquidity_usd"):
        if col not in df:
            df[col] = pd.NA
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["net_taker_flow_usd"] = df["buy_volume_usd"] - df["sell_volume_usd"]
    df["turnover_pct_mcap"] = df["volume_total_usd"] / df["market_cap_usd"].where(df["market_cap_usd"] > 0) * 100
    # Average ticket per side: a buy count that outnumbers sells says little
    # until you see whether the buyers are small and the sellers large.
    df["avg_buy_size_usd"] = df["buy_volume_usd"] / df["total_buys"].where(df["total_buys"] > 0)
    df["avg_sell_size_usd"] = df["sell_volume_usd"] / df["total_sells"].where(df["total_sells"] > 0)
    {{__df_name}} = df

    r = df.iloc[0]
    symbol = escape(str(r.get("symbol") or r.get("name") or TOKEN_ADDRESS[:10]))

    parts = []
    if pd.notna(r["market_cap_usd"]):
        parts.append(f"a ${r['market_cap_usd']:,.0f} market cap")
    if pd.notna(r["volume_total_usd"]):
        turn = f" ({r['turnover_pct_mcap']:.1f}% of market cap)" if pd.notna(r["turnover_pct_mcap"]) else ""
        parts.append(f"${r['volume_total_usd']:,.0f} traded over {TIMEFRAME}{turn}")
    if pd.notna(r["liquidity_usd"]):
        liq = f"${r['liquidity_usd']:,.0f} of pooled liquidity"
        if pd.notna(r["market_cap_usd"]) and r["market_cap_usd"] > 0:
            liq += f" ({r['liquidity_usd'] / r['market_cap_usd'] * 100:.1f}% of market cap)"
        parts.append(liq)
    lines = [f"{symbol} on {escape(CHAIN)} has " + ", ".join(parts) + "." if parts else f"{symbol} on {escape(CHAIN)} returned no market figures."]

    trades = (r["total_buys"] or 0) + (r["total_sells"] or 0) if pd.notna(r["total_buys"]) and pd.notna(r["total_sells"]) else 0
    if trades < 20 or pd.isna(r["avg_buy_size_usd"]) or pd.isna(r["avg_sell_size_usd"]):
        lines.append(f"Only {int(trades)} trades in the window, too few to compare buyer and seller sizes.")
    else:
        ratio = r["avg_sell_size_usd"] / r["avg_buy_size_usd"] if r["avg_buy_size_usd"] > 0 else float("inf")
        buyers = f"{int(r['unique_buyers'])} buyers" if pd.notna(r["unique_buyers"]) else "its buyers"
        sellers = f"{int(r['unique_sellers'])} sellers" if pd.notna(r["unique_sellers"]) else "its sellers"
        sizes = (
            f"Average buy is ${r['avg_buy_size_usd']:,.0f} across {buyers} versus "
            f"${r['avg_sell_size_usd']:,.0f} across {sellers}"
        )
        if ratio >= 2:
            lines.append(sizes + ": a few larger wallets are selling into many smaller buyers.")
        elif ratio <= 0.5:
            lines.append(sizes + ": a few larger wallets are buying while many smaller ones sell.")
        else:
            lines.append(sizes + ": buyers and sellers are similar in size, so no wallet-size asymmetry.")

    show(
        card("".join(f"<p>{line}</p>" for line in lines), f"{symbol} snapshot"),
        note("Figures are point-in-time and cached by Nansen for up to 5 minutes."),
    )
else:
    show(note("Nansen returned no information for this token on this chain."))
