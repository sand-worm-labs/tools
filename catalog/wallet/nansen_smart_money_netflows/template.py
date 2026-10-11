# Sandworm Power Toolbox — {{__tool_name}}
import os
from html import escape

import pandas as pd
import requests
from sandworm_theme import card, kpi_row, note, show, use_theme

use_theme()

CHAINS = "{{chains}}"
TOKEN_ADDRESS = "{{token_address}}".strip()
INCLUDE_LABELS = "{{include_smart_money_labels}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "all", "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "hyperevm",
    "iotaevm", "linea", "mantle", "monad", "optimism", "plasma", "polygon",
    "robinhood", "sei", "solana", "sonic",
}
ALLOWED_LABELS = {"Fund", "Smart Trader", "30D Smart Trader", "90D Smart Trader", "180D Smart Trader", "Smart HL Perps Trader"}
ALLOWED_SORT_FIELDS = {
    "chain", "token_address", "token_symbol", "net_flow_1h_usd", "net_flow_24h_usd",
    "net_flow_7d_usd", "net_flow_30d_usd", "token_sectors", "trader_count",
    "token_age_days", "market_cap_usd",
}

chains = [c.strip() for c in CHAINS.split(",") if c.strip()]
if not chains:
    raise ValueError("chains is required")
for c in chains:
    if c not in ALLOWED_CHAINS:
        raise ValueError(f"Unsupported chain: {c!r}")
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
if TOKEN_ADDRESS:
    filters["token_address"] = TOKEN_ADDRESS
if labels:
    filters["include_smart_money_labels"] = labels

body = {
    "chains": chains,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if filters:
    body["filters"] = filters

response = requests.post(
    "https://api.nansen.ai/api/v1/smart-money/netflow",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=30,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

# Raw netflow alone just says "how much $ moved" — these columns turn that into
# a conviction/trend read: flow sized per trader (a few whales vs a broad
# cohort buying read very differently) and flow sized against market cap (the
# same $ matters far more on a micro-cap than a blue chip).
if not {{__df_name}}.empty:
    {{__df_name}}["flow_per_trader_24h_usd"] = {{__df_name}}["net_flow_24h_usd"] / {{__df_name}}["trader_count"].replace(0, pd.NA)
    {{__df_name}}["flow_intensity_30d_pct_mcap"] = (
        {{__df_name}}["net_flow_30d_usd"] / {{__df_name}}["market_cap_usd"].replace(0, pd.NA) * 100
    )

    def _trend(row):
        h24, d7, d30 = row["net_flow_24h_usd"], row["net_flow_7d_usd"], row["net_flow_30d_usd"]
        if h24 > 0 and d7 > 0 and d30 > 0:
            return "sustained_accumulation"
        if h24 < 0 and d7 < 0 and d30 < 0:
            return "sustained_distribution"
        if h24 > 0 and d7 < 0:
            return "reversing_to_buy"
        if h24 < 0 and d7 > 0:
            return "reversing_to_sell"
        return "mixed"

    {{__df_name}}["smart_money_trend"] = {{__df_name}}.apply(_trend, axis=1)
    {{__df_name}} = {{__df_name}}.sort_values("flow_intensity_30d_pct_mcap", ascending=False, na_position="last").reset_index(drop=True)

    sized = {{__df_name}}.dropna(subset=["flow_intensity_30d_pct_mcap"])
    mix = {{__df_name}}["smart_money_trend"].value_counts()
    buying = {{__df_name}}.loc[{{__df_name}}["smart_money_trend"] == "reversing_to_buy", "token_symbol"].head(5).tolist()
    selling = {{__df_name}}.loc[{{__df_name}}["smart_money_trend"] == "reversing_to_sell", "token_symbol"].head(5).tolist()

    kpis = [
        ("Tokens analysed", len({{__df_name}})),
        ("Sustained accumulation", int(mix.get("sustained_accumulation", 0)), "pos"),
        ("Reversing to buy", int(mix.get("reversing_to_buy", 0)), "pos"),
        ("Sustained distribution", int(mix.get("sustained_distribution", 0)), "neg"),
    ]
    findings = []
    if not sized.empty:
        top = sized.iloc[0]
        findings.append(
            f"Strongest conviction: {escape(str(top['token_symbol']))}, with 30d smart-money net flow equal to "
            f"{top['flow_intensity_30d_pct_mcap']:.2f}% of its market cap."
        )
    if buying:
        findings.append("Turning to buy after a week of selling: " + escape(", ".join(map(str, buying))) + ".")
    if selling:
        findings.append("Turning to sell after a week of buying: " + escape(", ".join(map(str, selling))) + ".")
    insight = card("<ul>" + "".join(f"<li>{f}</li>" for f in findings) + "</ul>", "What stands out") if findings else ""

    show(
        kpi_row(kpis),
        insight,
        note("Trend compares the sign of 24h, 7d and 30d smart-money net flow. Flow intensity is 30d net flow as a % of market cap."),
    )

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.head(25),
        x="token_symbol",
        y="flow_intensity_30d_pct_mcap",
        color="smart_money_trend",
        title="Smart money 30d flow intensity (% of market cap)",
    )
    fig.show()
else:
    show(note("No smart-money netflow data matched these filters."))
