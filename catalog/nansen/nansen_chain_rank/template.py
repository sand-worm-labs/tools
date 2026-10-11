# Sandworm Power Toolbox — {{__tool_name}}
import os
from html import escape

import pandas as pd
import requests
from sandworm_theme import card, kpi_row, note, show, use_theme

use_theme()

TIME_FRAME = "{{time_frame}}".strip()
CHAIN_TYPE = "{{chain_type}}"

ALLOWED_TIME_FRAMES = {"7", "30", "365"}
ALLOWED_CHAIN_TYPES = {"all", "evm"}

if TIME_FRAME not in ALLOWED_TIME_FRAMES:
    raise ValueError(f"Unsupported time_frame: {TIME_FRAME!r}")
if CHAIN_TYPE not in ALLOWED_CHAIN_TYPES:
    raise ValueError(f"Unsupported chain_type: {CHAIN_TYPE!r}")

body = {
    "time_frame": int(TIME_FRAME),
    "chain_type": CHAIN_TYPE,
}

response = requests.post(
    "https://api.nansen.ai/api/v1/chains/chain-rank",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=90,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))


def _num(col):
    if col in {{__df_name}}:
        return pd.to_numeric({{__df_name}}[col], errors="coerce")
    return pd.Series(float("nan"), index={{__df_name}}.index)


# Each metric alone is a ranking anyone can read off a dashboard. The useful
# read is where two of them disagree: capital arriving with users leaving,
# users arriving with capital leaving, or traffic rising while revenue falls.
# Thresholds (+/-10%, TVL >= $1M, >= 1,000 txs) keep tiny chains' noisy
# percentages from being reported as signals.
if not {{__df_name}}.empty:
    tvl_chg = _num("tvl_usd_percent_change")
    users_chg = _num("active_address_count_txs_percent_change")
    tx_chg = _num("transaction_count_percent_change")
    rev_chg = _num("revenue_usd_percent_change")
    big_tvl = _num("tvl_usd") >= 1_000_000
    busy = _num("transaction_count") >= 1_000

    {{__df_name}}["divergence"] = "none"
    {{__df_name}}.loc[big_tvl & (tvl_chg >= 10) & (users_chg <= -10), "divergence"] = "capital_without_users"
    {{__df_name}}.loc[big_tvl & (users_chg >= 10) & (tvl_chg <= -10), "divergence"] = "users_without_capital"
    {{__df_name}}.loc[busy & (tx_chg >= 10) & (rev_chg <= -10) & ({{__df_name}}["divergence"] == "none"), "divergence"] = "usage_without_revenue"
    if "total_gas_used_usd" in {{__df_name}}:
        {{__df_name}} = {{__df_name}}.sort_values("total_gas_used_usd", ascending=False, na_position="last").reset_index(drop=True)

    tvl_chg, users_chg = _num("tvl_usd_percent_change"), _num("active_address_count_txs_percent_change")
    tx_chg, rev_chg = _num("transaction_count_percent_change"), _num("revenue_usd_percent_change")

    chain_names = {{__df_name}}["chain"].astype(str)

    def _list(kind, a, b, limit=3):
        idx = {{__df_name}}.index[{{__df_name}}["divergence"] == kind][:limit]
        return ", ".join(f"{escape(chain_names[i])} ({a[i]:+.0f}% vs {b[i]:+.0f}%)" for i in idx)

    counts = {{__df_name}}["divergence"].value_counts()
    days = TIME_FRAME
    findings = []
    if counts.get("capital_without_users", 0):
        findings.append(
            f"Capital without users over {days}d (TVL vs active addresses): "
            f"{_list('capital_without_users', tvl_chg, users_chg)}. Deposits growing while people leave is "
            "often incentive-driven rather than organic demand."
        )
    if counts.get("users_without_capital", 0):
        findings.append(
            f"Users without capital over {days}d (active addresses vs TVL): "
            f"{_list('users_without_capital', users_chg, tvl_chg)}. Activity is growing while liquidity drains."
        )
    if counts.get("usage_without_revenue", 0):
        findings.append(
            f"More transactions, less revenue over {days}d (transactions vs revenue): "
            f"{_list('usage_without_revenue', tx_chg, rev_chg)}. Fees per transaction are compressing."
        )
    if not findings:
        findings.append(f"No chain shows a 10%+ split between TVL, users, and revenue over {days}d; the metrics move together.")

    show(
        kpi_row([
            ("Chains ranked", len({{__df_name}})),
            ("Capital without users", int(counts.get("capital_without_users", 0)), "neg"),
            ("Users without capital", int(counts.get("users_without_capital", 0)), "neg"),
            ("Usage without revenue", int(counts.get("usage_without_revenue", 0)), "neg"),
        ]),
        card("<ul>" + "".join(f"<li>{f}</li>" for f in findings) + "</ul>", "What stands out"),
        note("Divergence needs two metrics to move 10%+ in opposite directions. Chains under $1M TVL (or 1,000 transactions for the revenue check) are skipped as too small to trust."),
    )

    import plotly.express as px

    plot = {{__df_name}}.assign(tvl_chg=tvl_chg, users_chg=users_chg).dropna(subset=["tvl_chg", "users_chg"])
    if len(plot) >= 2:
        fig = px.scatter(
            plot,
            x="users_chg",
            y="tvl_chg",
            color="divergence",
            hover_name="chain",
            labels={"users_chg": "Active addresses change (%)", "tvl_chg": "TVL change (%)"},
            title=f"TVL vs active-address change, last {days} days",
        )
        fig.show()
else:
    show(note("No chain-rank data came back for these filters."))
