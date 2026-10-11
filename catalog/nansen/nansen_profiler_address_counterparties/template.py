# Sandworm Power Toolbox — {{__tool_name}}
import os
from html import escape

import pandas as pd
import requests
from sandworm_theme import card, kpi_row, note, show, use_theme

use_theme()

ADDRESS = "{{address}}".strip()
ENTITY_NAME = "{{entity_name}}".strip()
CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()
SOURCE_INPUT = "{{source_input}}"
GROUP_BY = "{{group_by}}"
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "all", "arbitrum", "arc", "avalanche", "base", "bitcoin", "bnb", "ethereum",
    "hyperevm", "injective", "iotaevm", "linea", "mantle", "mantra", "monad",
    "near", "optimism", "plasma", "polygon", "robinhood", "sei", "solana",
    "sonic", "starknet", "sui", "ton", "tron",
}
ALLOWED_SOURCE_INPUTS = {"Combined", "Tokens", "ETH"}
ALLOWED_GROUP_BY = {"wallet", "entity"}
ALLOWED_SORT_FIELDS = {"interaction_count", "total_volume_usd", "volume_in_usd", "volume_out_usd"}

if not ADDRESS and not ENTITY_NAME:
    raise ValueError("Either address or entity_name is required")
if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_FROM or not DATE_TO:
    raise ValueError("date_from and date_to are required")
if SOURCE_INPUT not in ALLOWED_SOURCE_INPUTS:
    raise ValueError(f"Unsupported source_input: {SOURCE_INPUT!r}")
if GROUP_BY not in ALLOWED_GROUP_BY:
    raise ValueError(f"Unsupported group_by: {GROUP_BY!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

body = {
    "chain": CHAIN,
    "date": {"from": DATE_FROM, "to": DATE_TO},
    "source_input": SOURCE_INPUT,
    "group_by": GROUP_BY,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if ADDRESS:
    body["address"] = ADDRESS
if ENTITY_NAME:
    body["entity_name"] = ENTITY_NAME

response = requests.post(
    "https://api.nansen.ai/api/v1/profiler/address/counterparties",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

payload = response.json()
{{__df_name}} = pd.DataFrame(payload.get("data", []))
is_last_page = payload.get("pagination", {}).get("is_last_page", True)

if not {{__df_name}}.empty:
    for col in ("interaction_count", "total_volume_usd", "volume_in_usd", "volume_out_usd"):
        {{__df_name}}[col] = pd.to_numeric({{__df_name}}[col], errors="coerce").fillna(0)
    {{__df_name}}["net_flow_usd"] = {{__df_name}}["volume_in_usd"] - {{__df_name}}["volume_out_usd"]
    bigger = {{__df_name}}[["volume_in_usd", "volume_out_usd"]].max(axis=1)
    {{__df_name}}["reciprocity"] = {{__df_name}}[["volume_in_usd", "volume_out_usd"]].min(axis=1) / bigger.where(bigger > 0)

    def label_of(value):
        if isinstance(value, (list, tuple)):
            return ", ".join(str(v) for v in value[:2])
        return str(value) if isinstance(value, str) and value.strip() else ""

    zero = "0x0000000000000000000000000000000000000000"
    rows = {{__df_name}}[{{__df_name}}["counterparty_address"] != zero].copy()
    rows["label_text"] = rows["counterparty_address_label"].map(label_of) if "counterparty_address_label" in rows.columns else ""
    rows["labelled"] = rows["label_text"] != ""
    short = lambda a: f"{str(a)[:6]}…{str(a)[-4:]}"
    who = lambda r: escape(short(r["counterparty_address"])) + (f" ({escape(r['label_text'])})" if r["labelled"] else " (unlabelled)")
    total_volume = float(rows["total_volume_usd"].sum())
    unlabelled = rows[~rows["labelled"]]

    findings = []
    # Below $1,000 on both sides, back-and-forth flow is as likely to be dust or spam as a real link.
    mirror = unlabelled[
        (unlabelled["volume_in_usd"] >= 1000) & (unlabelled["volume_out_usd"] >= 1000)
        & (unlabelled["reciprocity"] >= 0.8) & (unlabelled["interaction_count"] >= 4)
    ].sort_values("total_volume_usd", ascending=False)
    if len(mirror):
        top = mirror.iloc[0]
        findings.append(
            f"{who(top)} sent back {top['reciprocity']:.0%} as much as it received (${top['volume_in_usd']:,.0f} in, "
            f"${top['volume_out_usd']:,.0f} out, {int(top['interaction_count'])} interactions). Near-symmetric flow with an "
            "unlabelled address is the signature of a linked wallet, a round-trip or a market maker."
        )
    sink = unlabelled[
        (unlabelled["volume_out_usd"] >= 1000) & (unlabelled["volume_in_usd"] < 0.05 * unlabelled["volume_out_usd"])
    ].sort_values("volume_out_usd", ascending=False)
    total_out = float(rows["volume_out_usd"].sum())
    if len(sink) and total_out > 0 and sink.iloc[0]["volume_out_usd"] / total_out >= 0.2:
        top = sink.iloc[0]
        findings.append(
            f"{who(top)} took ${top['volume_out_usd']:,.0f}, {top['volume_out_usd'] / total_out:.0%} of everything sent, and returned almost nothing: "
            "worth checking as a private cash-out or consolidation wallet."
        )
    chatty = unlabelled[(unlabelled["interaction_count"] >= 50)].sort_values("interaction_count", ascending=False)
    if len(chatty):
        top = chatty.iloc[0]
        average = top["total_volume_usd"] / top["interaction_count"]
        if average <= 10:
            findings.append(
                f"{who(top)} has {int(top['interaction_count']):,} interactions averaging ${average:,.2f}: that pattern looks like a bot, router or spam sender, not a relationship."
            )
    if len(rows) >= 3 and total_volume >= 100:
        lead = rows.sort_values("total_volume_usd", ascending=False).iloc[0]
        findings.append(
            f"The largest counterparty by volume is {who(lead)} with {lead['total_volume_usd'] / total_volume:.0%} of the ${total_volume:,.0f} moved."
        )
    if not findings:
        findings.append("No counterparty stands out: nothing mirrors the wallet's flow, absorbs its outflow or spams it.")
    if not is_last_page:
        findings.append("Only the first page of counterparties was fetched, so shares cover the fetched counterparties, not all of them.")

    show(
        kpi_row([
            ("Counterparties", len(rows)),
            ("Volume", f"${total_volume:,.0f}"),
            ("Unlabelled share of volume", f"{(float(unlabelled['total_volume_usd'].sum()) / total_volume):.0%}" if total_volume else "n/a"),
            ("Mirror-flow addresses", len(mirror)),
        ]),
        card("<ul>" + "".join(f"<li>{f}</li>" for f in findings) + "</ul>", "What stands out"),
        note("Reciprocity is the smaller of volume in and out divided by the larger: 1 means flows are perfectly symmetric. Labelled addresses (exchanges, protocols) are not flagged."),
    )

    import plotly.express as px

    chart = rows.sort_values("total_volume_usd", ascending=False).head(50)
    fig = px.scatter(
        chart,
        x="volume_out_usd",
        y="volume_in_usd",
        size="interaction_count",
        color=chart["labelled"].map({True: "labelled", False: "unlabelled"}),
        hover_name="counterparty_address",
        title="Counterparties: volume sent vs volume received (diagonal = symmetric flow)",
    )
    fig.show()
else:
    show(note("No counterparties found for this address in the chosen period."))
