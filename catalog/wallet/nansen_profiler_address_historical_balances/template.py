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
DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()
HIDE_SPAM_TOKENS = "{{hide_spam_tokens}}".strip().lower()
TOKEN_SYMBOL = "{{token_symbol}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "all", "arbitrum", "arc", "avalanche", "base", "bitcoin", "bnb", "ethereum",
    "hyperevm", "injective", "iotaevm", "linea", "mantle", "mantra", "monad",
    "near", "optimism", "plasma", "polygon", "robinhood", "sei", "solana",
    "sonic", "starknet", "sui", "ton", "tron",
}
ALLOWED_SORT_FIELDS = {"block_timestamp", "value_usd", "token_symbol"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS and not ENTITY_NAME:
    raise ValueError("Either address or entity_name is required")
if not DATE_FROM or not DATE_TO:
    raise ValueError("date_from and date_to are required")
if HIDE_SPAM_TOKENS not in {"true", "false"}:
    raise ValueError(f"Invalid hide_spam_tokens: {HIDE_SPAM_TOKENS!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

filters = {"hide_spam_tokens": HIDE_SPAM_TOKENS == "true"}
if TOKEN_SYMBOL:
    filters["token_symbol"] = TOKEN_SYMBOL

body = {
    "chain": CHAIN,
    "date": {"from": DATE_FROM, "to": DATE_TO},
    "filters": filters,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if ADDRESS:
    body["address"] = ADDRESS
if ENTITY_NAME:
    body["entity_name"] = ENTITY_NAME

response = requests.post(
    "https://api.nansen.ai/api/v1/profiler/address/historical-balances",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

payload = response.json()
{{__df_name}} = pd.DataFrame(payload.get("data", []))
is_last_page = payload.get("pagination", {}).get("is_last_page", True)

if not {{__df_name}}.empty:
    for col in ("token_amount", "value_usd"):
        {{__df_name}}[col] = pd.to_numeric({{__df_name}}[col], errors="coerce")
    {{__df_name}} = {{__df_name}}.sort_values("block_timestamp").reset_index(drop=True)
    {{__df_name}}["implied_price_usd"] = {{__df_name}}["value_usd"] / {{__df_name}}["token_amount"].where({{__df_name}}["token_amount"] > 0)

    key = ["chain", "token_address"]
    snapshots = {{__df_name}}["block_timestamp"].nunique()
    first = {{__df_name}}.loc[{{__df_name}}.groupby(key)["block_timestamp"].idxmin()].set_index(key)
    last = {{__df_name}}.loc[{{__df_name}}.groupby(key)["block_timestamp"].idxmax()].set_index(key)
    both = first.join(last, lsuffix="_0", rsuffix="_1", how="inner")
    both = both[
        (both["block_timestamp_0"] != both["block_timestamp_1"])
        & (both["token_amount_0"] > 0)
        & both["implied_price_usd_0"].notna()
        & both["implied_price_usd_1"].notna()
    ].copy()

    if snapshots < 2 or both.empty:
        show(note("Fewer than two snapshots with a usable price were returned, so balance changes cannot be separated into price moves and trading."))
    else:
        # value_1 - value_0 = (amount_1 - amount_0) * price_0  +  amount_1 * (price_1 - price_0)
        both["flow_usd"] = (both["token_amount_1"] - both["token_amount_0"]) * both["implied_price_usd_0"]
        both["price_effect_usd"] = both["token_amount_1"] * (both["implied_price_usd_1"] - both["implied_price_usd_0"])
        both["amount_change_pct"] = (both["token_amount_1"] / both["token_amount_0"] - 1) * 100
        both["price_change_pct"] = (both["implied_price_usd_1"] / both["implied_price_usd_0"] - 1) * 100
        flow_total = float(both["flow_usd"].sum())
        price_total = float(both["price_effect_usd"].sum())
        value_change = flow_total + price_total
        symbol = lambda r: escape(str(r["token_symbol_1"]))
        usd = lambda x: f"{'+' if x >= 0 else '-'}${abs(x):,.0f}"

        findings = []
        if max(abs(flow_total), abs(price_total)) >= 100:
            verb = "rose" if value_change >= 0 else "fell"
            action = "buying" if flow_total >= 0 else "selling"
            findings.append(
                f"Across {len(both)} tokens held at both ends of the window, value {verb} ${abs(value_change):,.0f}: "
                f"{usd(price_total)} came from price moves and {usd(flow_total)} from the wallet actively {action} tokens."
            )
            if (flow_total < 0) != (value_change < 0) and abs(flow_total) >= 100:
                findings.append(
                    "The wallet's trading and its value moved in opposite directions: price, not the wallet's decisions, drove the result."
                )
        active = both[(both["flow_usd"].abs() >= 100) & (both["amount_change_pct"].abs() >= 10)]
        if not active.empty:
            top = active.loc[active["flow_usd"].abs().idxmax()]
            cut = top["flow_usd"] < 0
            into = "into a rally" if (cut and top["price_change_pct"] > 0) else "into a drop" if (not cut and top["price_change_pct"] < 0) else "alongside a move"
            findings.append(
                f"Biggest deliberate move: {'cut' if cut else 'added to'} {symbol(top)} by {abs(top['amount_change_pct']):.0f}% "
                f"(about ${abs(top['flow_usd']):,.0f} at the starting price) {into}, as its price moved {top['price_change_pct']:+.0f}%."
            )
        else:
            findings.append("No token's balance changed by more than 10% (and $100), so the wallet looked passive over this window.")
        if not is_last_page:
            findings.append("Only the first page of snapshots was fetched, so the first and last balances per token may not be the true window ends.")

        show(
            kpi_row([
                ("Snapshots", snapshots),
                ("Tokens compared", len(both)),
                ("Value change", usd(value_change), "pos" if value_change >= 0 else "neg"),
                ("Net trading flow", usd(flow_total), "pos" if flow_total >= 0 else "neg"),
            ]),
            card("<ul>" + "".join(f"<li>{f}</li>" for f in findings) + "</ul>", "What stands out"),
            note("Each token's change is split into price effect (new price on the final amount) and trading flow (amount change at the starting price). Tokens missing a price at either end are excluded."),
        )

        import plotly.express as px

        top_symbols = {{__df_name}}.groupby("token_symbol")["value_usd"].max().nlargest(8).index
        fig = px.area(
            {{__df_name}}[{{__df_name}}["token_symbol"].isin(top_symbols)],
            x="block_timestamp",
            y="value_usd",
            color="token_symbol",
            title="Balance value over time (top 8 tokens)",
        )
        fig.show()
else:
    show(note("No balance snapshots found for this address in the chosen period."))
