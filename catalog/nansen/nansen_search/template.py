# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

SEARCH_QUERY = "{{search_query}}".strip()
RESULT_TYPE = "{{result_type}}"
CHAIN = "{{chain}}".strip()
LIMIT = "{{limit}}".strip()

ALLOWED_RESULT_TYPES = {"any", "token", "entity"}

if not (1 <= len(SEARCH_QUERY) <= 200):
    raise ValueError("search_query must be 1-200 characters")
if RESULT_TYPE not in ALLOWED_RESULT_TYPES:
    raise ValueError(f"Unsupported result_type: {RESULT_TYPE!r}")
if not LIMIT.isdigit() or not (1 <= int(LIMIT) <= 50):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

body = {
    "search_query": SEARCH_QUERY,
    "result_type": RESULT_TYPE,
    "limit": int(LIMIT),
}
if CHAIN:
    body["chain"] = CHAIN

response = requests.post(
    "https://api.nansen.ai/api/v1/search/general",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

# No "data" envelope here: the response has separate "tokens" and "entities" arrays.
payload = response.json()
tokens_df = pd.DataFrame(payload.get("tokens", []))
entities_df = pd.DataFrame(payload.get("entities", []))
if not tokens_df.empty:
    tokens_df["result_kind"] = "token"
    # Volume alone or market cap alone doesn't say how "hot" a token is relative
    # to its size; dividing the two gives a turnover read neither field shows on its own.
    if "volume_24h" in tokens_df.columns and "market_cap" in tokens_df.columns:
        tokens_df["turnover_24h_pct_mcap"] = (
            tokens_df["volume_24h"] / tokens_df["market_cap"].replace(0, pd.NA) * 100
        )
if not entities_df.empty:
    entities_df["result_kind"] = "entity"

{{__df_name}} = pd.concat([tokens_df, entities_df], ignore_index=True)
{{__df_name}}
