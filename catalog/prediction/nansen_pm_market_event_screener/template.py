# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests

QUERY = "{{query}}".strip()
STATUS = "{{status}}"
TAGS = "{{tags}}".strip()
MIN_LIQUIDITY = "{{min_liquidity}}".strip()
MAX_LIQUIDITY = "{{max_liquidity}}".strip()
MIN_VOLUME_24HR = "{{min_volume_24hr}}".strip()
MIN_OPEN_INTEREST = "{{min_open_interest}}".strip()
MAX_OPEN_INTEREST = "{{max_open_interest}}".strip()
MAX_UNIQUE_TRADERS_24H = "{{max_unique_traders_24h}}".strip()
NEG_RISK = "{{neg_risk}}"
END_DATE_AFTER = "{{end_date_after}}".strip()
END_DATE_BEFORE = "{{end_date_before}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_STATUS = {"", "active", "closed"}
ALLOWED_NEG_RISK = {"", "true", "false"}
ALLOWED_SORT_FIELDS = {
    "volume_24hr", "volume", "volume_1wk", "volume_1mo", "liquidity",
    "open_interest", "unique_traders_24h", "age_hours",
}

if len(QUERY) > 200:
    raise ValueError("query must be at most 200 characters")
if STATUS not in ALLOWED_STATUS:
    raise ValueError(f"Unsupported status: {STATUS!r}")

tags = [t.strip() for t in TAGS.split(",") if t.strip()]
if len(tags) > 50:
    raise ValueError("tags accepts at most 50 values")


def parse_bound(name, raw, integer=False):
    try:
        value = int(raw) if integer else float(raw)
    except ValueError:
        raise ValueError(f"Invalid {name}: {raw!r}")
    if value < -1:
        raise ValueError(f"{name} must be -1 (no filter) or greater")
    return value


min_liquidity = parse_bound("min_liquidity", MIN_LIQUIDITY)
max_liquidity = parse_bound("max_liquidity", MAX_LIQUIDITY)
min_volume_24hr = parse_bound("min_volume_24hr", MIN_VOLUME_24HR)
min_open_interest = parse_bound("min_open_interest", MIN_OPEN_INTEREST)
max_open_interest = parse_bound("max_open_interest", MAX_OPEN_INTEREST)
max_unique_traders_24h = parse_bound("max_unique_traders_24h", MAX_UNIQUE_TRADERS_24H, integer=True)

if NEG_RISK not in ALLOWED_NEG_RISK:
    raise ValueError(f"Unsupported neg_risk: {NEG_RISK!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

body = {
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if QUERY:
    body["query"] = QUERY
if STATUS:
    body["status"] = STATUS
if tags:
    body["tags"] = tags
if min_liquidity != -1:
    body["min_liquidity"] = min_liquidity
if max_liquidity != -1:
    body["max_liquidity"] = max_liquidity
if min_volume_24hr != -1:
    body["min_volume_24hr"] = min_volume_24hr
if min_open_interest != -1:
    body["min_open_interest"] = min_open_interest
if max_open_interest != -1:
    body["max_open_interest"] = max_open_interest
if max_unique_traders_24h != -1:
    body["max_unique_traders_24h"] = max_unique_traders_24h
if NEG_RISK:
    body["neg_risk"] = NEG_RISK == "true"
if END_DATE_AFTER:
    body["end_date_after"] = END_DATE_AFTER
if END_DATE_BEFORE:
    body["end_date_before"] = END_DATE_BEFORE

response = requests.post(
    "https://api.nansen.ai/api/v1/prediction-market/event-screener",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

if not {{__df_name}}.empty:
    {{__df_name}}["volume_to_liquidity_ratio"] = {{__df_name}}["total_volume_24hr"] / {{__df_name}}["total_liquidity"].replace(0, pd.NA)
    {{__df_name}}["top_market_share_pct"] = (
        {{__df_name}}["top_market_volume_24hr"] / {{__df_name}}["total_volume_24hr"].replace(0, pd.NA) * 100
    )
    {{__df_name}}["fragile_move"] = (
        {{__df_name}}["total_volume_change_pct"].abs() > {{__df_name}}["total_volume_change_pct"].abs().median()
    ) & ({{__df_name}}["total_liquidity"] < {{__df_name}}["total_liquidity"].median())

    import plotly.express as px

    fig = px.bar(
        {{__df_name}}.head(25),
        x="event_title",
        y="total_volume_24hr",
        color="fragile_move",
        title="Top prediction market events by 24h volume (flagging thin-liquidity swings)",
    )
    fig.show()

{{__df_name}}
