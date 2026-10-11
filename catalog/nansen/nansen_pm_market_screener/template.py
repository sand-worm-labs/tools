# Sandworm Power Toolbox — {{__tool_name}}
import os
from html import escape

import pandas as pd
import requests
from sandworm_theme import card, kpi_row, note, show, use_theme

use_theme()

QUERY = "{{query}}".strip()
STATUS = "{{status}}"
TAGS = "{{tags}}".strip()
MIN_LIQUIDITY = "{{min_liquidity}}".strip()
MAX_LIQUIDITY = "{{max_liquidity}}".strip()
MIN_VOLUME_24HR = "{{min_volume_24hr}}".strip()
MIN_OPEN_INTEREST = "{{min_open_interest}}".strip()
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


def parse_bound(name, raw):
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"Invalid {name}: {raw!r}")
    if value < -1:
        raise ValueError(f"{name} must be -1 (no filter) or greater")
    return value


min_liquidity = parse_bound("min_liquidity", MIN_LIQUIDITY)
max_liquidity = parse_bound("max_liquidity", MAX_LIQUIDITY)
min_volume_24hr = parse_bound("min_volume_24hr", MIN_VOLUME_24HR)
min_open_interest = parse_bound("min_open_interest", MIN_OPEN_INTEREST)

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
if NEG_RISK:
    body["neg_risk"] = NEG_RISK == "true"
if END_DATE_AFTER:
    body["end_date_after"] = END_DATE_AFTER
if END_DATE_BEFORE:
    body["end_date_before"] = END_DATE_BEFORE

response = requests.post(
    "https://api.nansen.ai/api/v1/prediction-market/market-screener",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

payload = response.json()
{{__df_name}} = pd.DataFrame(payload.get("data", []))
is_last_page = bool(payload.get("pagination", {}).get("is_last_page", True))

if not {{__df_name}}.empty:
    for col in ("last_trade_price", "one_day_price_change", "volume_24hr", "volume_1wk", "unique_traders_24h"):
        {{__df_name}}[col] = pd.to_numeric({{__df_name}}[col], errors="coerce") if col in {{__df_name}} else float("nan")
    # Nansen reports 0 for markets with no trader data, so 0 is treated as unknown rather than "nobody traded".
    {{__df_name}}["unique_traders_24h"] = {{__df_name}}["unique_traders_24h"].where({{__df_name}}["unique_traders_24h"] > 0)
    for col in ("question", "closed"):
        if col not in {{__df_name}}:
            {{__df_name}}[col] = pd.NA

    # one_day_price_change is read as an absolute change on the 0-1 price scale (Polymarket's oneDayPriceChange).
    {{__df_name}}["move_pts"] = {{__df_name}}["one_day_price_change"] * 100
    daily_norm = {{__df_name}}["volume_1wk"] / 7
    {{__df_name}}["volume_vs_norm"] = {{__df_name}}["volume_24hr"] / daily_norm.where(daily_norm > 0)
    is_live = ~{{__df_name}}["closed"].fillna(False).astype(bool)
    {{__df_name}}["thin_move"] = (
        is_live
        & ({{__df_name}}["move_pts"].abs() >= 10)
        & (({{__df_name}}["volume_vs_norm"] < 0.5) | ({{__df_name}}["unique_traders_24h"] <= 5))
    )

    big = {{__df_name}}[is_live & ({{__df_name}}["move_pts"].abs() >= 10)]
    thin = {{__df_name}}[{{__df_name}}["thin_move"]].sort_values("move_pts", key=lambda s: s.abs(), ascending=False)

    findings = []
    if len(thin):
        examples = []
        for r in thin.head(3).itertuples():
            how = []
            if pd.notna(r.volume_vs_norm):
                how.append(f"{r.volume_vs_norm:.0%} of its usual daily volume")
            if pd.notna(r.unique_traders_24h):
                how.append(f"{int(r.unique_traders_24h)} traders")
            to = f" to {r.last_trade_price * 100:.0f}%" if pd.notna(r.last_trade_price) else ""
            examples.append(f"'{escape(str(r.question))}' ({r.move_pts:+.0f} pts{to}, on {' and '.join(how)})")
        findings.append(
            f"{len(thin)} of the {len(big)} markets that moved 10+ points in a day did so on thin participation, "
            "so those moves are the likeliest to reverse: " + "; ".join(examples) + "."
        )
    elif len(big):
        findings.append(f"All {len(big)} markets that moved 10+ points in a day did so on normal volume, so the moves look backed by real participation.")
    else:
        findings.append("No open market in this screen moved 10+ points in the last day.")
    if not is_last_page:
        findings.append(f"Only the first {len({{__df_name}})} markets by the chosen sort were fetched, so moves elsewhere are not covered.")

    show(
        kpi_row([
            ("Markets screened", len({{__df_name}})),
            ("Moved 10+ points in 24h", len(big)),
            ("...on thin participation", len(thin), "neg" if len(thin) else ""),
        ]),
        card("<ul>" + "".join(f"<li>{f}</li>" for f in findings) + "</ul>", "What stands out"),
        note("Move is the 24h change in last-trade price, in points. Thin means 24h volume under half the market's own 7-day daily average, or 5 or fewer reported unique traders (a count of 0 is treated as missing). Closed markets are excluded."),
    )

    plot = {{__df_name}}[is_live].dropna(subset=["move_pts", "volume_vs_norm"])
    if len(plot) >= 2:
        import plotly.express as px

        fig = px.scatter(
            plot,
            x="volume_vs_norm",
            y="move_pts",
            color="thin_move",
            hover_name="question",
            title="24h price move vs volume relative to the market's own norm",
            labels={"volume_vs_norm": "24h volume / usual daily volume", "move_pts": "24h move (points)"},
        )
        fig.show()
else:
    show(note("No prediction markets matched these filters."))
