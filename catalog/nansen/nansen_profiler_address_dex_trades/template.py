# Sandworm Power Toolbox — {{__tool_name}}
import os
from html import escape

import pandas as pd
import requests
from sandworm_theme import card, kpi_row, note, show, use_theme

use_theme()

ADDRESS = "{{address}}".strip()
CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()
TOKEN_BOUGHT_SYMBOL = "{{token_bought_symbol}}".strip()
TOKEN_SOLD_SYMBOL = "{{token_sold_symbol}}".strip()
MIN_TRADE_VALUE_USD = "{{min_trade_value_usd}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "hyperevm",
    "injective", "iotaevm", "linea", "mantle", "mantra", "monad", "near",
    "optimism", "plasma", "polygon", "robinhood", "sei", "solana", "sonic",
    "starknet", "sui", "ton", "tron",
}
ALLOWED_SORT_FIELDS = {"block_timestamp", "trade_value_usd"}

if not ADDRESS:
    raise ValueError("address is required")
if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_FROM or not DATE_TO:
    raise ValueError("date_from and date_to are required")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

filters = {}
if TOKEN_BOUGHT_SYMBOL:
    filters["token_bought_symbol"] = TOKEN_BOUGHT_SYMBOL
if TOKEN_SOLD_SYMBOL:
    filters["token_sold_symbol"] = TOKEN_SOLD_SYMBOL
if MIN_TRADE_VALUE_USD:
    filters["trade_value_usd"] = {"min": float(MIN_TRADE_VALUE_USD)}

body = {
    "address": ADDRESS,
    "chain": CHAIN,
    "date": {"from": DATE_FROM, "to": DATE_TO},
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if filters:
    body["filters"] = filters

response = requests.post(
    "https://api.nansen.ai/api/v1/profiler/dex-trades",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

payload = response.json()
{{__df_name}} = pd.DataFrame(payload.get("data", []))
is_last_page = payload.get("pagination", {}).get("is_last_page", True)

if not {{__df_name}}.empty:
    for col in ("trade_value_usd", "token_bought_age_days", "token_sold_age_days"):
        if col not in {{__df_name}}.columns:
            {{__df_name}}[col] = pd.NA
        {{__df_name}}[col] = pd.to_numeric({{__df_name}}[col], errors="coerce")
    {{__df_name}} = {{__df_name}}.sort_values("block_timestamp").reset_index(drop=True)
    {{__df_name}}["trade_date"] = {{__df_name}}["block_timestamp"].astype(str).str[:10]

    def tag(symbols, addresses):
        symbols = symbols.astype("object")
        return symbols.where(symbols.notna() & (symbols != ""), addresses.astype(str).str[:6] + "…")

    # Under $100 is usually dust or address-poisoning noise; it should not drive conclusions.
    priced = {{__df_name}}[{{__df_name}}["trade_value_usd"].fillna(0) >= 100].copy()
    if priced.empty:
        show(note("Trades were returned but none are worth at least $100, so no pattern is reported."))
    else:
        priced["bought"] = tag(priced["token_bought_symbol"], priced["token_bought_address"])
        priced["sold"] = tag(priced["token_sold_symbol"], priced["token_sold_address"])
        volume = float(priced["trade_value_usd"].sum())
        net = priced.groupby("bought")["trade_value_usd"].sum().sub(priced.groupby("sold")["trade_value_usd"].sum(), fill_value=0)
        days = priced.groupby("trade_date")["trade_value_usd"].sum()

        findings = []
        if len(priced) >= 3 and len(net) >= 2:
            buy, fund = net.idxmax(), net.idxmin()
            if net[buy] >= 100 and net[fund] <= -100:
                buy_trades = int((priced["bought"] == buy).sum())
                findings.append(
                    f"Net buying is concentrated in {escape(str(buy))} (+${net[buy]:,.0f} over {buy_trades} buy trades), "
                    f"largely funded by selling {escape(str(fund))} (-${abs(net[fund]):,.0f})."
                )
        aged = priced.dropna(subset=["token_bought_age_days"])
        if len(aged) >= 5:
            fresh_share = float(aged.loc[aged["token_bought_age_days"] < 30, "trade_value_usd"].sum() / aged["trade_value_usd"].sum())
            findings.append(
                f"{fresh_share:.0%} of buy volume went into tokens under 30 days old "
                f"(median age of bought tokens: {aged['token_bought_age_days'].median():.0f} days)."
            )
        if len(priced) >= 5 and len(days) >= 2 and days.max() / volume >= 0.5:
            findings.append(f"Activity is bursty: {days.max() / volume:.0%} of the ${volume:,.0f} traded happened on {escape(str(days.idxmax()))}.")
        if not findings:
            findings.append(f"{len(priced)} trade(s) worth ${volume:,.0f} in total, with no dominant token, age pattern or burst of activity.")
        if not is_last_page:
            findings.append("Only the first page of trades was fetched, so these patterns cover the fetched trades, not the whole period.")

        show(
            kpi_row([
                ("Trades analysed", len(priced)),
                ("Volume", f"${volume:,.0f}"),
                ("Tokens touched", len(net)),
                ("Active days", len(days)),
            ]),
            card("<ul>" + "".join(f"<li>{f}</li>" for f in findings) + "</ul>", "What stands out"),
            note("Net flow per token is USD bought minus USD sold across the fetched trades. Trades under $100 are ignored."),
        )

        import plotly.express as px

        extremes = pd.concat([net.nlargest(5), net.nsmallest(5)]).groupby(level=0).first().sort_values()
        fig = px.bar(
            x=extremes.values,
            y=extremes.index,
            orientation="h",
            color=(extremes.values >= 0),
            color_discrete_map={True: "#2e9e6b", False: "#d4543f"},
            labels={"x": "Net USD bought minus sold", "y": "Token", "color": "Net buying"},
            title="Net token flow from DEX trades",
        )
        fig.show()
else:
    show(note("No DEX trades found for this address in the chosen period."))
