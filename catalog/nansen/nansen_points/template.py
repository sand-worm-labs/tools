# Sandworm Power Toolbox — {{__tool_name}}
import pandas as pd
import requests

ADDRESS = "{{address}}".strip()
TIER = "{{tier}}"
PAGE = "{{page}}".strip()
RECORDS_PER_PAGE = "{{records_per_page}}".strip()

ALLOWED_TIERS = {"all", "green", "ice", "north", "star"}

if ADDRESS and not ADDRESS.isalnum():
    raise ValueError(f"Invalid address: {ADDRESS!r}")
if TIER not in ALLOWED_TIERS:
    raise ValueError(f"Unsupported tier: {TIER!r}")
if not PAGE.isdigit() or int(PAGE) < 1:
    raise ValueError(f"Invalid page: {PAGE!r}")
if not RECORDS_PER_PAGE.isdigit() or not (1 <= int(RECORDS_PER_PAGE) <= 10000):
    raise ValueError(f"Invalid records_per_page: {RECORDS_PER_PAGE!r}")

# This endpoint lives on app.nansen.ai (not api.nansen.ai) and is explicitly
# public per the docs, with no apikey header.
if ADDRESS:
    response = requests.get(
        f"https://app.nansen.ai/api/points-leaderboard/{ADDRESS}",
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()
    {{__df_name}} = pd.DataFrame([{
        "address": ADDRESS,
        "rank": payload.get("rank"),
        "points": payload.get("points"),
        "evm_address": payload.get("evm_address"),
        "solana_address": payload.get("solana_address"),
        "tier": payload.get("tier"),
        "is_eligible": payload.get("is_eligible"),
        "points_gap_to_leader_pct": None,
    }])
else:
    params = {"page": int(PAGE), "recordsPerPage": int(RECORDS_PER_PAGE)}
    if TIER != "all":
        params["tier"] = TIER

    response = requests.get(
        "https://app.nansen.ai/api/points-leaderboard/api",
        params=params,
        timeout=90,
    )
    response.raise_for_status()

    {{__df_name}} = pd.DataFrame(response.json().get("results", []))
    {{__df_name}}["address"] = None

    # How far each wallet is from the page leader, since raw point totals
    # alone don't say whether 2nd place is close or far behind.
    if not {{__df_name}}.empty:
        leader_points = {{__df_name}}["points"].max()
        {{__df_name}}["points_gap_to_leader_pct"] = (
            (leader_points - {{__df_name}}["points"]) / leader_points * 100 if leader_points else None
        )

        import plotly.express as px

        fig = px.bar({{__df_name}}, x="rank", y="points", color="tier", title="Nansen points leaderboard")
        fig.show()

{{__df_name}}
