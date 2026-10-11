# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests
from html import escape
from sandworm_theme import card, kpi_row, note, show, use_theme

use_theme()

CHAIN = "{{chain}}".strip()
TOKEN_ADDRESSES = "{{token_addresses}}".strip()
TIMEFRAME = "{{timeframe}}"
DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()

ALLOWED_CHAINS = {
    "algorand", "aptos", "arbitrum", "arc", "avalanche", "base", "bitcoin",
    "bitlayer", "bnb", "chiliz", "ethereum", "gravity", "hyperevm", "hyperliquid",
    "injective", "iotaevm", "linea", "mantle", "mantra", "monad", "near",
    "optimism", "plasma", "polygon", "robinhood", "sei", "solana", "sonic",
    "stacks", "starknet", "stellar", "sui", "ton", "tron", "viction",
}
ALLOWED_TIMEFRAMES = {"1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w", "1M"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if TIMEFRAME not in ALLOWED_TIMEFRAMES:
    raise ValueError(f"Unsupported timeframe: {TIMEFRAME!r}")

addresses = [a.strip() for a in TOKEN_ADDRESSES.split(",") if a.strip()]
if not addresses:
    raise ValueError("token_addresses is required")
max_addresses = 5 if CHAIN == "hyperliquid" else 10
if len(addresses) > max_addresses:
    raise ValueError(f"Too many token_addresses for chain {CHAIN!r}: max {max_addresses}")

body = {"chain": CHAIN, "timeframe": TIMEFRAME}
if len(addresses) == 1:
    body["token_address"] = addresses[0]
else:
    body["token_addresses"] = addresses

date_range = {}
if DATE_FROM:
    date_range["from"] = DATE_FROM
if DATE_TO:
    date_range["to"] = DATE_TO
if date_range:
    body["date"] = date_range

response = requests.post(
    "https://api.nansen.ai/api/v1/tgm/token-ohlcv",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

payload = response.json()


def _flatten(token_address, candle):
    market_cap = candle.get("market_cap", {}) or {}
    return {
        "chain": payload.get("chain"),
        "timeframe": payload.get("timeframe"),
        "token_address": token_address,
        "interval_start": candle.get("interval_start"),
        "open": candle.get("open"),
        "high": candle.get("high"),
        "low": candle.get("low"),
        "close": candle.get("close"),
        "volume": candle.get("volume"),
        "volume_usd": candle.get("volume_usd"),
        "market_cap_open": market_cap.get("open"),
        "market_cap_high": market_cap.get("high"),
        "market_cap_low": market_cap.get("low"),
        "market_cap_close": market_cap.get("close"),
    }


rows = []
if "tokens" in payload:
    for token in payload.get("tokens", []) or []:
        for candle in token.get("data", []) or []:
            rows.append(_flatten(token.get("token_address"), candle))
else:
    for candle in payload.get("data", []) or []:
        rows.append(_flatten(payload.get("token_address"), candle))

{{__df_name}} = pd.DataFrame(rows)
for _col in ["open", "high", "low", "close", "volume", "volume_usd", "market_cap_open", "market_cap_high", "market_cap_low", "market_cap_close"]:
    if _col in {{__df_name}}:
        {{__df_name}}[_col] = pd.to_numeric({{__df_name}}[_col], errors="coerce")

if not {{__df_name}}.empty:
    import numpy as np

    df = {{__df_name}}.sort_values(["token_address", "interval_start"]).reset_index(drop=True)
    grouped_close = df.groupby("token_address")["close"]
    df["cumulative_return_pct"] = (df["close"] / grouped_close.transform("first") - 1) * 100
    df["drawdown_pct"] = (df["close"] / grouped_close.cummax() - 1) * 100
    {{__df_name}} = df

    short = lambda a: f"{str(a)[:6]}…{str(a)[-4:]}"
    when = lambda ts: str(ts)[:16].replace("T", " ")
    findings, scored = [], 0
    for token, g in df.groupby("token_address"):
        c = g.dropna(subset=["close"])
        c = c[c["close"] > 0]
        if len(c) < 3:
            continue
        scored += 1
        name = escape(short(token))
        first, last = c["close"].iloc[0], c["close"].iloc[-1]
        ret = last / first - 1

        # Market cap = price x circulating supply, so if the two moves disagree the
        # gap is supply growth (unlocks, emissions) that a price chart never shows.
        mc = c["market_cap_close"].dropna()
        mc = mc[mc > 0]
        if len(mc) >= 3:
            implied_supply = (mc.iloc[-1] / mc.iloc[0]) / (1 + ret) - 1
            if abs(implied_supply) >= 0.05:
                findings.append(
                    f"{name}: price moved {ret:+.1%} but market cap moved {mc.iloc[-1] / mc.iloc[0] - 1:+.1%}, "
                    f"which implies circulating supply changed by about {implied_supply:+.0%} over the window."
                )

        dd = c["close"] / c["close"].cummax() - 1
        trough = dd.idxmin()
        if dd[trough] <= -0.10:
            peak_ts = c.loc[c.loc[:trough, "close"].idxmax(), "interval_start"]
            findings.append(
                f"{name}: ended {ret:+.1%} over {len(c)} candles, but fell {dd[trough]:.0%} from its peak "
                f"({when(peak_ts)} to {when(c.loc[trough, 'interval_start'])}) on the way."
            )

        log_ret = np.log(c["close"]).diff().dropna()
        total = log_ret.sum()
        if len(log_ret) >= 10 and abs(total) >= 0.05:
            big = log_ret.abs().idxmax()
            share = log_ret[big] / total
            if share >= 0.6:
                findings.append(
                    f"{name}: {share:.0%} of the whole move came from the single candle at {when(c.loc[big, 'interval_start'])}, "
                    f"so this is a one-off spike, not a trend."
                )

    if not findings:
        findings.append(
            "No supply change, deep drawdown or single-candle spike stands out in this window."
            if scored else "Fewer than 3 usable candles per token, too few for a read."
        )
    if payload.get("truncated"):
        findings.append("Nansen truncated this response, so the window may be shorter than requested.")

    show(
        kpi_row([
            ("Tokens", df["token_address"].nunique()),
            ("Candles", len(df)),
            ("Best return", f"{df.groupby('token_address')['cumulative_return_pct'].last().max():+.1f}%"),
            ("Worst drawdown", f"{df['drawdown_pct'].min():.1f}%", "neg"),
        ]),
        card("<ul>" + "".join(f"<li>{f}</li>" for f in findings) + "</ul>", "What stands out"),
        note("Implied supply change compares market-cap return with price return. Drawdown is measured from the running peak close."),
    )

    import plotly.express as px

    fig = px.line(
        df, x="interval_start", y="cumulative_return_pct", color="token_address",
        title=f"{CHAIN} cumulative return ({TIMEFRAME})",
    )
    fig.show()
else:
    show(note("No candles came back for these tokens and dates."))
