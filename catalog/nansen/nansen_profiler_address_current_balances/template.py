# Sandworm Power Toolbox — {{__tool_name}}
import os
from html import escape

import pandas as pd
import requests
from sandworm_theme import card, kpi_row, note, show, use_theme

use_theme()

CHAIN = "{{chain}}"
ADDRESS = "{{address}}".strip()
ENTITY_NAME = "{{entity_name}}".strip()
HIDE_SPAM_TOKEN = "{{hide_spam_token}}".strip().lower()
TOKEN_SYMBOL = "{{token_symbol}}".strip()
MIN_VALUE_USD = "{{min_value_usd}}".strip()
MAX_VALUE_USD = "{{max_value_usd}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "all", "arbitrum", "arc", "avalanche", "base", "bitcoin", "bnb", "ethereum",
    "hyperevm", "injective", "iotaevm", "linea", "mantle", "mantra", "monad",
    "near", "optimism", "plasma", "polygon", "robinhood", "sei", "solana",
    "sonic", "starknet", "sui", "ton", "tron",
}
ALLOWED_SORT_FIELDS = {"value_usd", "token_symbol"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS and not ENTITY_NAME:
    raise ValueError("Either address or entity_name is required")
if HIDE_SPAM_TOKEN not in {"true", "false"}:
    raise ValueError(f"Invalid hide_spam_token: {HIDE_SPAM_TOKEN!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

value_usd_range = {}
if MIN_VALUE_USD:
    value_usd_range["min"] = float(MIN_VALUE_USD)
if MAX_VALUE_USD:
    value_usd_range["max"] = float(MAX_VALUE_USD)

filters = {}
if TOKEN_SYMBOL:
    filters["token_symbol"] = TOKEN_SYMBOL
if value_usd_range:
    filters["value_usd"] = value_usd_range

body = {
    "chain": CHAIN,
    "hide_spam_token": HIDE_SPAM_TOKEN == "true",
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if ADDRESS:
    body["address"] = ADDRESS
if ENTITY_NAME:
    body["entity_name"] = ENTITY_NAME
if filters:
    body["filters"] = filters

response = requests.post(
    "https://api.nansen.ai/api/v1/profiler/address/current-balance",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

payload = response.json()
{{__df_name}} = pd.DataFrame(payload.get("data", []))
is_last_page = payload.get("pagination", {}).get("is_last_page", True)

if not {{__df_name}}.empty:
    {{__df_name}} = {{__df_name}}.sort_values("value_usd", ascending=False, na_position="last").reset_index(drop=True)
    values = {{__df_name}}["value_usd"].fillna(0).clip(lower=0)
    total_value = float(values.sum())
    short = lambda a: f"{str(a)[:6]}…{str(a)[-4:]}"
    name = lambda r: escape(str(r["token_symbol"])) if pd.notna(r["token_symbol"]) and r["token_symbol"] else escape(short(r["token_address"]))

    if total_value <= 0:
        show(note("Balances were returned but none carry a USD price, so allocation cannot be measured."))
    else:
        {{__df_name}}["portfolio_pct"] = values / total_value * 100
        {{__df_name}}["cumulative_pct"] = {{__df_name}}["portfolio_pct"].cumsum()
        shares = values / total_value
        effective_positions = 1 / float((shares**2).sum())
        n_tokens = len({{__df_name}})
        top_n = min(3, n_tokens)
        top_share = float(shares.iloc[:top_n].sum())
        top_names = [name(r) for _, r in {{__df_name}}.head(top_n).iterrows()]
        dust = {{__df_name}}[{{__df_name}}["value_usd"].fillna(0) < 10]
        unpriced = int({{__df_name}}["value_usd"].isna().sum())

        findings = []
        if n_tokens == 1:
            findings.append(f"The whole portfolio (${total_value:,.0f}) is a single token: {top_names[0]}.")
        else:
            findings.append(
                f"{top_share:.0%} of this wallet's value sits in {top_n} token(s): " + ", ".join(top_names) + "."
            )
        if n_tokens >= 4:
            findings.append(
                f"It holds {n_tokens} tokens, but its concentration is equivalent to only {effective_positions:.1f} equally-sized positions."
            )
        if len(dust) >= 3 and len(dust) / n_tokens >= 0.5:
            findings.append(
                f"{len(dust)} of {n_tokens} tokens are worth under $10 each (${float(dust['value_usd'].fillna(0).sum()):,.0f} combined), "
                "which looks like airdrop or spam residue rather than real positions."
            )
        if {{__df_name}}["chain"].nunique() > 1:
            by_chain = {{__df_name}}.groupby("chain")["value_usd"].sum().sort_values(ascending=False)
            findings.append(f"{by_chain.iloc[0] / total_value:.0%} of value is on {escape(str(by_chain.index[0]))}.")
        if unpriced:
            findings.append(f"{unpriced} token(s) have no USD price and are left out of the shares above.")
        if not is_last_page:
            findings.append("Only the first page of balances was fetched, so shares are measured against the fetched tokens, not the whole wallet.")

        show(
            kpi_row([
                ("Total value", f"${total_value:,.0f}"),
                ("Tokens held", n_tokens),
                ("Top holding", f"{shares.iloc[0]:.0%}"),
                ("Effective positions", f"{effective_positions:.1f}"),
            ]),
            card("<ul>" + "".join(f"<li>{f}</li>" for f in findings) + "</ul>", "What stands out"),
            note("Effective positions is the inverse Herfindahl index: 1 means everything in one token, N means evenly spread over N tokens."),
        )

        import plotly.express as px

        chart = {{__df_name}}.head(10)[["token_symbol", "value_usd"]].copy()
        rest = float(values.iloc[10:].sum())
        if rest > 0:
            chart.loc[len(chart)] = ["Other", rest]
        fig = px.pie(chart, names="token_symbol", values="value_usd", title="Portfolio allocation")
        fig.show()
else:
    show(note("No balances found for this address or entity."))
