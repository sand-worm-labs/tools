# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests
from html import escape
from sandworm_theme import card, kpi_row, note, show, use_theme

use_theme()

CHAIN = "{{chain}}".strip()
TOKEN_ADDRESS = "{{token_address}}".strip()

ALLOWED_CHAINS = {
    "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "hyperevm",
    "hyperliquid", "injective", "iotaevm", "linea", "mantle", "mantra", "monad",
    "near", "optimism", "plasma", "polygon", "robinhood", "sei", "solana",
    "sonic", "starknet", "sui", "ton", "tron",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_ADDRESS:
    raise ValueError("token_address is required")

body = {
    "chain": CHAIN,
    "token_address": TOKEN_ADDRESS,
}

response = requests.post(
    "https://api.nansen.ai/api/v1/tgm/indicators",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

payload = response.json()
token_info = payload.get("token_info", {}) or {}

rows = []
for category, indicators in (
    ("risk", payload.get("risk_indicators", []) or []),
    ("reward", payload.get("reward_indicators", []) or []),
):
    for indicator in indicators:
        rows.append({
            "token_address": payload.get("token_address"),
            "chain": payload.get("chain"),
            "market_cap_usd": token_info.get("market_cap_usd"),
            "market_cap_group": token_info.get("market_cap_group"),
            "is_stablecoin": token_info.get("is_stablecoin"),
            "indicator_category": category,
            "indicator_type": indicator.get("indicator_type"),
            "score": indicator.get("score"),
            "signal": indicator.get("signal"),
            "signal_percentile": indicator.get("signal_percentile"),
            "last_trigger_on": indicator.get("last_trigger_on"),
        })

{{__df_name}} = pd.DataFrame(rows)

RISK_SCORES = {"low": 0, "medium": 1, "high": 2}
REWARD_SCORES = {"bearish": -1, "neutral": 0, "bullish": 1}

if not {{__df_name}}.empty:
    df = {{__df_name}}
    is_risk = df["indicator_category"] == "risk"
    risk_avg = df.loc[is_risk, "score"].map(RISK_SCORES).mean()
    reward_avg = df.loc[~is_risk, "score"].map(REWARD_SCORES).mean()
    risk_tier = "unknown" if pd.isna(risk_avg) else ("high" if risk_avg >= 1.5 else ("medium" if risk_avg >= 0.5 else "low"))
    reward_tier = "unknown" if pd.isna(reward_avg) else ("bullish" if reward_avg > 0.33 else ("bearish" if reward_avg < -0.33 else "neutral"))
    df["composite_risk_tier"] = risk_tier
    df["composite_reward_tier"] = reward_tier
    {{__df_name}} = df

    risks = df[is_risk]
    rewards = df[~is_risk]
    high_risk = risks[risks["score"] == "high"]["indicator_type"].drop_duplicates().tolist()
    bullish = rewards[rewards["score"] == "bullish"]["indicator_type"].drop_duplicates().tolist()
    bearish = rewards[rewards["score"] == "bearish"]["indicator_type"].drop_duplicates().tolist()
    group = df["market_cap_group"].dropna().iloc[0] if df["market_cap_group"].notna().any() else None
    stable = bool(df["is_stablecoin"].fillna(False).iloc[0])

    findings = []
    if stable:
        findings.append("Nansen classes this token as a stablecoin, so price-momentum style reward indicators say little about it.")
    findings.append(
        f"{len(high_risk)} of {len(risks)} risk indicators are rated high"
        + (f" ({escape(', '.join(high_risk))})" if high_risk else "")
        + f"; {len(bullish)} of {len(rewards)} reward indicators are bullish"
        + (f" ({escape(', '.join(bullish))})" if bullish else "")
        + (f" and {len(bearish)} bearish ({escape(', '.join(bearish))})" if bearish else "")
        + "."
    )
    if high_risk and bullish:
        findings.append(
            f"Reward signals lean up while {escape(high_risk[0])} is high risk, so any upside is likely to be fragile."
        )
    elif len(risks) and not high_risk and bullish and not bearish:
        findings.append("Risk and reward agree: no high-risk indicator against a bullish set of reward signals.")
    elif high_risk and bearish:
        findings.append(f"Both sides are negative: {escape(high_risk[0])} is high risk and {escape(bearish[0])} is bearish.")

    extreme = risks.dropna(subset=["signal_percentile"])
    extreme = extreme[extreme["signal_percentile"] >= 90].sort_values("signal_percentile", ascending=False)
    if len(extreme):
        top = extreme.iloc[0]
        peer = f"{escape(str(group))} tokens" if group else "tokens of similar size"
        findings.append(
            f"{escape(str(top['indicator_type']))} sits at the {top['signal_percentile']:.0f}th percentile of {peer} "
            f"(a high rank on a risk indicator)."
        )

    show(
        kpi_row([
            ("Risk tier", risk_tier, "neg" if risk_tier == "high" else ("pos" if risk_tier == "low" else None)),
            ("Reward tier", reward_tier, "pos" if reward_tier == "bullish" else ("neg" if reward_tier == "bearish" else None)),
            ("Market cap group", str(group) if group else "n/a"),
        ]),
        card("<ul>" + "".join(f"<li>{f}</li>" for f in findings) + "</ul>", "What stands out"),
        note("Tier averages the scores of each side (risk: low/medium/high, reward: bearish/neutral/bullish). Percentiles compare against tokens in the same market-cap group. Indicators refresh daily."),
    )

    import plotly.express as px

    fig = px.bar(
        df.dropna(subset=["signal_percentile"]),
        x="indicator_type",
        y="signal_percentile",
        color="indicator_category",
        title="Indicator percentile vs tokens of similar size",
    )
    fig.show()
else:
    show(note("Nansen returned no indicators for this token."))
