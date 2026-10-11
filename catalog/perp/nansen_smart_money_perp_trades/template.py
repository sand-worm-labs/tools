# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

LOOKBACK_HOURS = "{{lookback_hours}}".strip()
ONLY_NEW_POSITIONS = "{{only_new_positions}}"
TRADER_ADDRESS = "{{trader_address}}".strip()
TOKEN_SYMBOL = "{{token_symbol}}".strip()
SIDE = "{{side}}"
INCLUDE_LABELS = "{{include_smart_money_labels}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_LABELS = {"Fund", "Smart Trader", "30D Smart Trader", "90D Smart Trader", "180D Smart Trader", "Smart HL Perps Trader"}
ALLOWED_SORT_FIELDS = {"block_timestamp", "token_amount", "price_usd", "value_usd"}
ALLOWED_SIDES = {"any", "Long", "Short"}

if not LOOKBACK_HOURS.isdigit() or not (1 <= int(LOOKBACK_HOURS) <= 168):
    raise ValueError(f"Invalid lookback_hours: {LOOKBACK_HOURS!r}")
if ONLY_NEW_POSITIONS not in {"true", "false"}:
    raise ValueError(f"Invalid only_new_positions: {ONLY_NEW_POSITIONS!r}")
if SIDE not in ALLOWED_SIDES:
    raise ValueError(f"Unsupported side: {SIDE!r}")
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
if TOKEN_SYMBOL:
    filters["token_symbol"] = TOKEN_SYMBOL
if SIDE != "any":
    filters["side"] = SIDE
if labels:
    filters["include_smart_money_labels"] = labels

body = {
    "lookback_hours": int(LOOKBACK_HOURS),
    "only_new_positions": ONLY_NEW_POSITIONS == "true",
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if filters:
    body["filters"] = filters

response = requests.post(
    "https://api.nansen.ai/api/v1/smart-money/perp-trades",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

# Individual trades don't say whether smart money is net long or short on a
# token, or whether that bias is a few whales or many traders. Signing each
# trade's value by its action and aggregating by token surfaces both.
if not {{__df_name}}.empty:
    bullish_actions = {"Buy - Add Long", "Buy - Open Long", "Buy - Close Short", "Buy - Reduce Short"}
    bearish_actions = {"Sell - Add Short", "Sell - Open Short", "Sell - Close Long", "Sell - Reduce Long"}

    def _signed_value(row):
        value, action = row.get("value_usd"), row.get("action")
        if pd.isna(value):
            return None
        if action in bullish_actions:
            return value
        if action in bearish_actions:
            return -value
        return None

    {{__df_name}}["signed_value_usd"] = {{__df_name}}.apply(_signed_value, axis=1)

    token_flows = {{__df_name}}.groupby("token_symbol").agg(
        net_directional_flow_usd=("signed_value_usd", "sum"),
        trader_count=("trader_address", "nunique"),
    ).reset_index()
    token_flows["flow_per_trader_usd"] = (
        token_flows["net_directional_flow_usd"] / token_flows["trader_count"].replace(0, pd.NA)
    )

    {{__df_name}} = {{__df_name}}.merge(token_flows, on="token_symbol", how="left")
    {{__df_name}} = {{__df_name}}.sort_values("value_usd", ascending=False, na_position="last").reset_index(drop=True)

    import plotly.express as px

    fig = px.bar(
        token_flows.sort_values("net_directional_flow_usd", ascending=False),
        x="token_symbol",
        y="net_directional_flow_usd",
        title="Smart money perp net directional flow by token (USD)",
    )
    fig.show()

{{__df_name}}
