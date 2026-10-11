# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

CHAINS = "{{chains}}"
TIMEFRAME = "{{timeframe}}"
TOKEN_ADDRESS = "{{token_address}}".strip()
TRADER_TYPE = "{{trader_type}}"
SECTORS = "{{sectors}}".strip()
MARKET_CAP_MIN = "{{market_cap_min}}".strip()
MARKET_CAP_MAX = "{{market_cap_max}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "hyperevm",
    "hyperliquid", "injective", "iotaevm", "linea", "mantle", "mantra", "monad",
    "near", "optimism", "plasma", "polygon", "robinhood", "sei", "solana",
    "sonic", "starknet", "sui", "ton", "tron",
}
ALLOWED_TIMEFRAMES = {"5m", "10m", "1h", "6h", "24h", "7d", "30d"}
ALLOWED_TRADER_TYPES = {
    "all", "sm", "whale", "public_figure", "trending",
    "consistent_perps_winner", "high_winrate_hl_perps_trader", "predicted_winner",
}
ALLOWED_SORT_FIELDS = {
    "chain", "token_address", "token_symbol", "market_cap_usd", "volume",
    "liquidity", "nof_traders", "nof_buyers", "nof_sellers", "nof_buys",
    "nof_sells", "price_change", "price_usd", "netflow", "buy_volume",
    "sell_volume", "fdv", "fdv_mc_ratio", "inflow_fdv_ratio",
    "outflow_fdv_ratio", "token_age_days",
}

chains = [c.strip() for c in CHAINS.split(",") if c.strip()]
if not chains or len(chains) > 5:
    raise ValueError("chains is required, 1-5 values")
for c in chains:
    if c not in ALLOWED_CHAINS:
        raise ValueError(f"Unsupported chain: {c!r}")
if TIMEFRAME not in ALLOWED_TIMEFRAMES:
    raise ValueError(f"Unsupported timeframe: {TIMEFRAME!r}")
if TRADER_TYPE not in ALLOWED_TRADER_TYPES:
    raise ValueError(f"Unsupported trader_type: {TRADER_TYPE!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

token_addresses = [t.strip() for t in TOKEN_ADDRESS.split(",") if t.strip()]
sectors = [s.strip() for s in SECTORS.split(",") if s.strip()]

filters = {"trader_type": TRADER_TYPE}
if token_addresses:
    filters["token_address"] = token_addresses if len(token_addresses) > 1 else token_addresses[0]
if sectors:
    filters["sectors"] = sectors
if MARKET_CAP_MIN or MARKET_CAP_MAX:
    mcap_range = {}
    if MARKET_CAP_MIN:
        mcap_range["min"] = float(MARKET_CAP_MIN)
    if MARKET_CAP_MAX:
        mcap_range["max"] = float(MARKET_CAP_MAX)
    filters["market_cap_usd"] = mcap_range

body = {
    "chains": chains,
    "timeframe": TIMEFRAME,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "filters": filters,
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}

response = requests.post(
    "https://api.nansen.ai/api/v1/token-screener",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    # Conviction (netflow as a share of gross volume traded) vs size (netflow as a
    # share of market cap) — two tokens with identical $ netflow read very
    # differently once sized against how much they actually trade and how big they are.
    {{__df_name}}["netflow_pct_volume"] = (
        {{__df_name}}["netflow"] / {{__df_name}}["volume"].replace(0, pd.NA) * 100
    )
    {{__df_name}}["netflow_pct_mcap"] = (
        {{__df_name}}["netflow"] / {{__df_name}}["market_cap_usd"].replace(0, pd.NA) * 100
    )

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.head(25),
        x="token_symbol",
        y=SORT_FIELD,
        color="chain",
        title=f"Top tokens by {SORT_FIELD} ({TIMEFRAME})",
    )
    fig.show()

{{__df_name}}
