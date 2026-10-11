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
HIDE_SPAM_TOKEN = "{{hide_spam_token}}".strip().lower()
TOKEN_SYMBOL = "{{token_symbol}}".strip()
COUNTERPARTY_ADDRESS = "{{counterparty_address}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "all", "arbitrum", "arc", "avalanche", "base", "bitcoin", "bnb", "ethereum",
    "injective", "iotaevm", "linea", "mantle", "mantra", "monad", "near",
    "optimism", "plasma", "polygon", "robinhood", "sei", "solana", "sonic",
    "starknet", "sui", "ton", "tron",
}

if not ADDRESS:
    raise ValueError("address is required")
if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_FROM or not DATE_TO:
    raise ValueError("date_from and date_to are required")
if HIDE_SPAM_TOKEN not in {"true", "false"}:
    raise ValueError(f"Invalid hide_spam_token: {HIDE_SPAM_TOKEN!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 100):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

filters = {}
if TOKEN_SYMBOL:
    filters["token_symbol"] = TOKEN_SYMBOL
if COUNTERPARTY_ADDRESS:
    filters["counterparty_address"] = COUNTERPARTY_ADDRESS

body = {
    "address": ADDRESS,
    "chain": CHAIN,
    "date": {"from": DATE_FROM, "to": DATE_TO},
    "hide_spam_token": HIDE_SPAM_TOKEN == "true",
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": "block_timestamp", "direction": SORT_DIRECTION}],
}
if filters:
    body["filters"] = filters

response = requests.post(
    "https://api.nansen.ai/api/v1/profiler/address/transactions",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

payload = response.json()
{{__df_name}} = pd.DataFrame(payload.get("data", []))
is_last_page = payload.get("pagination", {}).get("is_last_page", True)

if not {{__df_name}}.empty:
    {{__df_name}}["volume_usd"] = pd.to_numeric({{__df_name}}["volume_usd"], errors="coerce").fillna(0)
    {{__df_name}} = {{__df_name}}.sort_values("block_timestamp").reset_index(drop=True)

    def _leg_usd(legs):
        return sum(float(leg.get("value_usd") or 0) for leg in legs) if isinstance(legs, list) else 0.0

    # Direction comes from the token legs, since `method` is a contract method name, not "sent"/"received".
    in_usd = {{__df_name}}["tokens_received"].map(_leg_usd) if "tokens_received" in {{__df_name}} else 0.0
    out_usd = {{__df_name}}["tokens_sent"].map(_leg_usd) if "tokens_sent" in {{__df_name}} else 0.0
    {{__df_name}}["signed_volume_usd"] = in_usd - out_usd
    {{__df_name}}["cumulative_net_usd"] = {{__df_name}}["signed_volume_usd"].cumsum()

    me = ADDRESS.lower()
    short = lambda a: f"{a[:6]}…{a[-4:]}"
    sent_to, received_from, names = {}, {}, {}
    for column, totals, who, who_label in (
        ("tokens_sent", sent_to, "to_address", "to_address_label"),
        ("tokens_received", received_from, "from_address", "from_address_label"),
    ):
        if column not in {{__df_name}}.columns:
            continue
        for legs in {{__df_name}}[column]:
            if not isinstance(legs, list):
                continue
            for leg in legs:
                other = str(leg.get(who) or "").lower()
                if not other or other == me:
                    continue
                totals[other] = totals.get(other, 0.0) + float(leg.get("value_usd") or 0)
                if leg.get(who_label):
                    names[other] = str(leg[who_label])

    total_sent, total_received = sum(sent_to.values()), sum(received_from.values())
    describe = lambda a: escape(short(a)) + (f" ({escape(names[a])})" if a in names else " (unlabelled)")

    findings = []
    # Dust-sized flows (and address-poisoning transfers) are ignored below $100.
    if len({{__df_name}}) >= 3 and total_sent >= 100:
        dest = max(sent_to, key=sent_to.get)
        share = sent_to[dest] / total_sent
        back = received_from.get(dest, 0.0)
        line = f"{share:.0%} of the ${total_sent:,.0f} this wallet sent went to one address, {describe(dest)}."
        if dest not in names and back < 0.05 * sent_to[dest] and share >= 0.4:
            line += " Nothing meaningful came back from it, which fits a private cash-out or consolidation wallet."
        findings.append(line)
    if len({{__df_name}}) >= 3 and total_received >= 100:
        origin = max(received_from, key=received_from.get)
        share = received_from[origin] / total_received
        findings.append(f"{share:.0%} of the ${total_received:,.0f} it received came from {describe(origin)}.")
    net = total_received - total_sent
    if abs(net) >= 100:
        findings.append(f"Net movement over the period: {'inflow' if net > 0 else 'outflow'} of ${abs(net):,.0f}.")
    if not findings:
        findings.append("Too few transactions of meaningful size to say where this wallet's money goes.")
    if not is_last_page:
        findings.append("Only the first page of transactions was fetched, so shares cover the fetched transactions, not the whole period.")

    show(
        kpi_row([
            ("Transactions", len({{__df_name}})),
            ("Received", f"${total_received:,.0f}", "pos"),
            ("Sent", f"${total_sent:,.0f}", "neg"),
            ("Counterparties", len(set(sent_to) | set(received_from))),
        ]),
        card("<ul>" + "".join(f"<li>{f}</li>" for f in findings) + "</ul>", "What stands out"),
        note("Shares are measured on the USD value of token legs per counterparty address; legs under $100 total are too small to read as a pattern."),
    )

    import plotly.express as px

    fig = px.line(
        {{__df_name}},
        x="block_timestamp",
        y="cumulative_net_usd",
        title="Cumulative net USD flow over time",
    )
    fig.show()
else:
    show(note("No transactions found for this address in the chosen period."))
