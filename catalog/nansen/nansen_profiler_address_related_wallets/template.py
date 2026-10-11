# Sandworm Power Toolbox — {{__tool_name}}
import os
from html import escape

import pandas as pd
import requests
from sandworm_theme import card, kpi_row, note, show, use_theme

use_theme()

WALLET_ADDRESS = "{{wallet_address}}".strip()
CHAIN = "{{chain}}"
PER_PAGE = "{{per_page}}".strip()
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "arbitrum", "arc", "avalanche", "base", "bitcoin", "bnb", "ethereum",
    "injective", "iotaevm", "linea", "mantle", "mantra", "monad", "near",
    "optimism", "plasma", "polygon", "robinhood", "sei", "solana", "sonic",
    "starknet", "sui", "ton", "tron",
}

if not WALLET_ADDRESS:
    raise ValueError("wallet_address is required")
if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

body = {
    "wallet_address": WALLET_ADDRESS,
    "chain": CHAIN,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": "order", "direction": SORT_DIRECTION}],
}

response = requests.post(
    "https://api.nansen.ai/api/v1/profiler/address/related-wallets",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

payload = response.json()
{{__df_name}} = pd.DataFrame(payload.get("data", []))
is_last_page = payload.get("pagination", {}).get("is_last_page", True)

if not {{__df_name}}.empty:
    {{__df_name}} = {{__df_name}}.sort_values("order").reset_index(drop=True)
    short = lambda a: f"{str(a)[:6]}…{str(a)[-4:]}"
    relations = {{__df_name}}["relation"].value_counts()
    named = {{__df_name}}[{{__df_name}}["address_label"].notna() & ({{__df_name}}["address_label"] != "")] if "address_label" in {{__df_name}}.columns else {{__df_name}}.iloc[0:0]

    sentences = [
        f"Nansen links {len({{__df_name}})} wallet(s) to {escape(short(WALLET_ADDRESS))}, by relation: "
        + ", ".join(f"{int(n)} {escape(str(r))}" for r, n in relations.items()) + "."
    ]
    if len(named):
        sentences.append(
            "Labelled among them: "
            + ", ".join(f"{escape(str(r['address_label']))} ({escape(short(r['address']))})" for _, r in named.head(3).iterrows())
            + "."
        )
    else:
        sentences.append("None of the related wallets carry a Nansen label.")
    sentences.append(f"The earliest link is dated {escape(str({{__df_name}}['block_timestamp'].min())[:10])}.")
    if not is_last_page:
        sentences.append("More related wallets exist beyond this page.")
    show(card("<p>" + " ".join(sentences) + "</p>", "Related wallets"))
else:
    show(note("Nansen has no related wallets for this address on this chain."))
