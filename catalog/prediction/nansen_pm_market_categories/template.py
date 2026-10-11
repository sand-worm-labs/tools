# Sandworm Power Toolbox — {{__tool_name}}
import os
from html import escape

import pandas as pd
import requests
from sandworm_theme import card, note, show, use_theme

use_theme()

PER_PAGE = "{{per_page}}".strip()

if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")

body = {
    "pagination": {
        "page": 1,
        "per_page": int(PER_PAGE),
    },
}

response = requests.post(
    "https://api.nansen.ai/api/v1/prediction-market/categories",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=30,
)
response.raise_for_status()

payload = response.json()
{{__df_name}} = pd.DataFrame(payload.get("data", []))
is_last_page = bool(payload.get("pagination", {}).get("is_last_page", True))

if not {{__df_name}}.empty:
    volume = pd.to_numeric({{__df_name}}.get("total_volume_24hr"), errors="coerce")
    ranked = {{__df_name}}.assign(_volume=volume).sort_values("_volume", ascending=False, na_position="last")
    parts = []
    for _, row in ranked.head(12).iterrows():
        label = escape(str(row["category"]))
        parts.append(f"{label} (${row['_volume']:,.0f} traded in 24h)" if pd.notna(row["_volume"]) else label)
    noun = "category" if len(ranked) == 1 else "categories"
    line = f"{len(ranked)} {noun}" + (" on this page" if not is_last_page else "")
    line += ", ranked by 24h volume: " + ", ".join(parts) + "."
    show(card(line, "Prediction market categories"))
else:
    show(note("No prediction market categories were returned."))
