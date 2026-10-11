# Sandworm Power Toolbox — {{__tool_name}}
import os
from html import escape

import pandas as pd
import requests
from sandworm_theme import card, kpi_row, note, show, use_theme

use_theme()

ADDRESS = "{{address}}".strip()
CHAIN = "{{chain}}"
PER_PAGE = "{{per_page}}".strip()

ALLOWED_CHAINS = {
    "all", "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "hyperevm",
    "hyperliquid", "iotaevm", "linea", "mantle", "monad", "optimism", "plasma",
    "polygon", "robinhood", "sei", "solana", "sonic", "tron",
}

if not ADDRESS:
    raise ValueError("address is required")
if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")

body = {
    "address": ADDRESS,
    "chain": CHAIN,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
}

response = requests.post(
    "https://api.nansen.ai/api/v1/profiler/address/labels",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

payload = response.json()
{{__df_name}} = pd.DataFrame(payload.get("data", []))
is_last_page = payload.get("pagination", {}).get("is_last_page", True)

short = f"{ADDRESS[:6]}…{ADDRESS[-4:]}"
if not {{__df_name}}.empty:
    parts = []
    for _, r in {{__df_name}}.iterrows():
        category = r.get("category")
        parts.append(escape(str(r["label"])) + (f" ({escape(str(category))})" if pd.notna(category) and category else ""))
    sentence = f"Nansen labels {escape(short)} as: " + ", ".join(parts) + "."
    if not is_last_page:
        sentence += " More labels exist beyond this page."
    show(card("<p>" + sentence + "</p>", "Address labels"))
else:
    hint = payload.get("hint")
    show(note("Nansen has no non-premium labels for this address." + (f" {hint}" if hint else "")))
