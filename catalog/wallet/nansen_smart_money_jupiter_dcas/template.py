# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

TRADER_ADDRESS = "{{trader_address}}".strip()
OUTPUT_TOKEN_SYMBOL = "{{output_token_symbol}}".strip()
DCA_CREATED_FROM = "{{dca_created_from}}".strip()
DCA_CREATED_TO = "{{dca_created_to}}".strip()
INCLUDE_LABELS = "{{include_smart_money_labels}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_LABELS = {"Fund", "Smart Trader", "30D Smart Trader", "90D Smart Trader", "180D Smart Trader", "Smart HL Perps Trader"}
ALLOWED_SORT_FIELDS = {
    "dca_created_at", "dca_updated_at", "input_token_symbol", "output_token_symbol",
    "deposit_token_amount", "token_spent_amount", "deposit_value_usd", "output_token_redeemed_amount",
}

if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

labels = [label.strip() for label in INCLUDE_LABELS.split(",") if label.strip()]
for label in labels:
    if label not in ALLOWED_LABELS:
        raise ValueError(f"Unsupported smart money label: {label!r}")

filters = {}
if TRADER_ADDRESS:
    filters["trader_address"] = TRADER_ADDRESS
if OUTPUT_TOKEN_SYMBOL:
    filters["output_token_symbol"] = OUTPUT_TOKEN_SYMBOL
if labels:
    filters["include_smart_money_labels"] = labels
if DCA_CREATED_FROM or DCA_CREATED_TO:
    date_range = {}
    if DCA_CREATED_FROM:
        date_range["from"] = DCA_CREATED_FROM
    if DCA_CREATED_TO:
        date_range["to"] = DCA_CREATED_TO
    filters["dca_created_at"] = date_range

body = {
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if filters:
    body["filters"] = filters

response = requests.post(
    "https://api.nansen.ai/api/v1/smart-money/dcas",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

# Neither field exists on its own in the response: completion % (spent vs.
# planned deposit) and the implied average USD price paid (value vs. amount
# spent) both come from combining two raw amounts.
if not {{__df_name}}.empty:
    {{__df_name}}["dca_completion_pct"] = (
        {{__df_name}}["token_spent_amount"] / {{__df_name}}["deposit_token_amount"].replace(0, pd.NA) * 100
    )
    {{__df_name}}["implied_avg_price_usd"] = (
        {{__df_name}}["deposit_value_usd"] / {{__df_name}}["token_spent_amount"].replace(0, pd.NA)
    )
    {{__df_name}} = {{__df_name}}.sort_values("deposit_value_usd", ascending=False, na_position="last").reset_index(drop=True)

    import plotly.express as px

    fig = px.scatter(
        {{__df_name}},
        x="dca_completion_pct",
        y="deposit_value_usd",
        color="dca_status",
        hover_data=["output_token_symbol", "trader_address_label"],
        title="Smart money Jupiter DCAs: plan completion vs. deposit size",
    )
    fig.show()

{{__df_name}}
