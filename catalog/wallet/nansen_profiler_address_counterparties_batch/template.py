# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests
from html import escape
from sandworm_theme import card, kpi_row, note, show, use_theme

use_theme()

WALLET_ADDRESSES = "{{wallet_addresses}}"
CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}".strip()
DATE_TO = "{{date_to}}".strip()
SOURCE_INPUT = "{{source_input}}"
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
ALLOWED_SORT_FIELDS = {"interaction_count", "total_volume_usd", "volume_in_usd", "volume_out_usd"}

wallet_addresses = [a.strip() for a in WALLET_ADDRESSES.split(",") if a.strip()]
if not wallet_addresses:
    raise ValueError("wallet_addresses is required")
if len(wallet_addresses) > 10:
    raise ValueError("wallet_addresses supports at most 10 addresses")
if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_FROM or not DATE_TO:
    raise ValueError("date_from and date_to are required")
if SOURCE_INPUT not in ALLOWED_SOURCE_INPUTS:
    raise ValueError(f"Unsupported source_input: {SOURCE_INPUT!r}")
if not PER_PAGE.isdigit() or not (1 <= int(PER_PAGE) <= 1000):
    raise ValueError(f"Invalid per_page: {PER_PAGE!r}")
if SORT_FIELD not in ALLOWED_SORT_FIELDS:
    raise ValueError(f"Unsupported sort_field: {SORT_FIELD!r}")
if SORT_DIRECTION not in {"ASC", "DESC"}:
    raise ValueError(f"Unsupported sort_direction: {SORT_DIRECTION!r}")

body = {
    "wallet_addresses": wallet_addresses,
    "chain": CHAIN,
    "date": {"from": DATE_FROM, "to": DATE_TO},
    "source_input": SOURCE_INPUT,
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}

response = requests.post(
    "https://api.nansen.ai/api/v1/profiler/address/counterparties/batch",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=30,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

# Rows come back as contiguous per-wallet blocks with very different scales,
# so "many touches, tiny value" (likely a bot/router) vs "few touches, huge
# value" (a real relationship) has to be judged against each wallet's own
# medians, not a global cutoff.
if not {{__df_name}}.empty:
    {{__df_name}}["net_flow_usd"] = {{__df_name}}["volume_in_usd"] - {{__df_name}}["volume_out_usd"]
    volume_per_interaction = {{__df_name}}["total_volume_usd"] / {{__df_name}}["interaction_count"].replace(0, pd.NA)
    median_interactions = {{__df_name}}.groupby("wallet_address")["interaction_count"].transform("median")
    median_vpi = volume_per_interaction.groupby({{__df_name}}["wallet_address"]).transform("median")

    def _relationship(count, vpi, med_count, med_vpi):
        if count > med_count and vpi < med_vpi:
            return "likely_bot_or_router"
        if count <= med_count and vpi >= med_vpi:
            return "key_relationship"
        return "typical"

    {{__df_name}}["relationship_type"] = [
        _relationship(c, v, mc, mv)
        for c, v, mc, mv in zip(
            {{__df_name}}["interaction_count"], volume_per_interaction, median_interactions, median_vpi
        )
    ]

    zero = "0x0000000000000000000000000000000000000000"
    wallets_set = {w.lower() for w in wallet_addresses}
    rows = {{__df_name}}[{{__df_name}}["counterparty_address"] != zero].copy()
    rows["labelled"] = rows["counterparty_address_label"].notna()
    short = lambda a: f"{a[:6]}…{a[-4:]}"

    by_cp = rows.groupby("counterparty_address").agg(
        wallets=("wallet_address", "nunique"), labelled=("labelled", "max"), volume_usd=("total_volume_usd", "sum")
    ).reset_index()
    shared = by_cp[by_cp["wallets"] >= 2]
    shared_unlabelled = shared[~shared["labelled"]].sort_values(["wallets", "volume_usd"], ascending=False)
    internal = rows[rows["counterparty_address"].isin(wallets_set)].sort_values("total_volume_usd", ascending=False)
    internal_usd = float(internal["total_volume_usd"].sum())

    # Everyone touches exchanges and routers, so overlap is measured on unlabelled counterparties only.
    sets = {w: set(g["counterparty_address"]) for w, g in rows[~rows["labelled"]].groupby("wallet_address")}
    names = [w.lower() for w in wallet_addresses]
    sets = {w: sets.get(w, set()) for w in names}
    overlap = pd.DataFrame(
        [[len(sets[a] & sets[b]) / len(sets[a] | sets[b]) if (sets[a] | sets[b]) else 0.0 for b in names] for a in names],
        index=[short(n) for n in names], columns=[short(n) for n in names],
    )
    pairs = [overlap.iat[i, j] for i in range(len(names)) for j in range(i + 1, len(names))]
    mean_overlap = sum(pairs) / len(pairs) if pairs else 0.0
    meaningful_flow = internal_usd >= 100  # smaller transfers are usually dust or address-poisoning spam
    linked = meaningful_flow or mean_overlap >= 0.15

    findings = []
    if len(internal):
        top = internal.iloc[0]
        findings.append(
            f"These wallets transact directly with each other: {len(internal)} flows worth ${internal_usd:,.0f}. "
            f"Largest is {escape(short(top['wallet_address']))} with {escape(short(top['counterparty_address']))} (${top['total_volume_usd']:,.0f})."
            + ("" if meaningful_flow else " That is dust-sized, so it is not treated as evidence of common ownership.")
        )
    if len(shared_unlabelled):
        top = shared_unlabelled.iloc[0]
        findings.append(
            f"{len(shared_unlabelled)} unlabelled address(es) are used by two or more of your wallets. The busiest, "
            f"{escape(short(top['counterparty_address']))}, is shared by {int(top['wallets'])} of {len(names)} wallets (${top['volume_usd']:,.0f} combined)."
        )
    findings.append(f"Average overlap in unlabelled counterparties between wallet pairs is {mean_overlap:.0%}.")
    if not response.json().get("pagination", {}).get("is_last_page", True):
        findings.append("Only the top counterparties per the chosen sort were fetched, so some shared contacts may be missed.")

    show(
        kpi_row([
            ("Wallets analysed", len(names)),
            ("Shared counterparties", len(shared)),
            ("Shared and unlabelled", len(shared_unlabelled)),
            ("Direct transfers between wallets", f"${internal_usd:,.0f}"),
        ]),
        card("<ul>" + "".join(f"<li>{f}</li>" for f in findings) + "</ul>",
             "Verdict: likely connected" if linked else "Verdict: look independent"),
        note("Shared counterparties are addresses that two or more of these wallets deal with. Labelled addresses (exchanges, protocols) are excluded from the overlap score."),
    )

    if len(names) >= 2:
        import plotly.express as px

        fig = px.imshow(overlap, text_auto=".0%", zmin=0, zmax=1, title="Shared unlabelled counterparties between wallets")
        fig.show()
else:
    show(note("No counterparties found for these wallets in the chosen period."))
