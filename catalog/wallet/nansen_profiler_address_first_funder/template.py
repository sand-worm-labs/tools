# Sandworm Power Toolbox — {{__tool_name}}
import os
from html import escape

import pandas as pd
import requests
from sandworm_theme import card, kpi_row, note, show, use_theme

use_theme()

ADDRESS = "{{address}}".strip()

if not ADDRESS:
    raise ValueError("address is required")

body = {
    "address": ADDRESS,
    "chain": "all",
}

response = requests.post(
    "https://api.nansen.ai/api/v1/profiler/address/first-funder",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=30,
)
response.raise_for_status()

payload = response.json()
{{__df_name}} = pd.DataFrame(payload.get("data", []))

if not {{__df_name}}.empty:
    short = lambda a: f"{str(a)[:6]}…{str(a)[-4:]}"
    sentences = []
    for _, r in {{__df_name}}.head(3).iterrows():
        name = r.get("first_funder_name")
        who = escape(short(r["first_funder_address"])) + (f" ({escape(str(name))})" if pd.notna(name) and name else ", an unlabelled address")
        sentences.append(
            f"{escape(short(r['wallet_address']))} was first funded by {who} on {escape(str(r['block_timestamp'])[:10])} "
            f"on {escape(str(r['chain']))} (transaction {escape(short(r['transaction_hash']))})."
        )
    show(card("<p>" + " ".join(sentences) + "</p>", "First funder"))
else:
    show(note("Nansen has no first-funder record for this address."))
