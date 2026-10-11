# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

ADDRESS = "{{address}}".strip()
PER_PAGE = "{{per_page}}".strip()

if not (1 <= len(ADDRESS) <= 100):
    raise ValueError("address must be 1-100 characters")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")

body = {
    "address": ADDRESS,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
}

response = requests.post(
    "https://api.nansen.ai/api/v1/prediction-market/address-summary",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    {{__df_name}}["win_rate_pct"] = {{__df_name}}["win_rate"] * 100
    {{__df_name}}["realized_pnl_share_pct"] = (
        {{__df_name}}["realized_pnl_usd"] / {{__df_name}}["total_pnl_usd"].replace(0, pd.NA) * 100
    )
    {{__df_name}}["small_sample_win_rate"] = ({{__df_name}}["win_rate"] > 0.7) & ({{__df_name}}["markets_traded"] < 5)

{{__df_name}}
