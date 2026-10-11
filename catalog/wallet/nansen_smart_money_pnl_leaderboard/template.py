# Sandworm Power Toolbox — {{__tool_name}}
import os

import pandas as pd
import requests
from html import escape
from sandworm_theme import card, kpi_row, note, show, use_theme

use_theme()

CHAINS = "{{chains}}"
TIMEFRAME = "{{timeframe}}".strip()
INCLUDE_LABELS = "{{include_smart_money_labels}}".strip()
PER_PAGE = "{{per_page}}".strip()
SORT_FIELD = "{{sort_field}}"
SORT_DIRECTION = "{{sort_direction}}"

ALLOWED_CHAINS = {
    "all", "arbitrum", "arc", "avalanche", "base", "bnb", "ethereum", "hyperevm",
    "iotaevm", "linea", "mantle", "monad", "optimism", "plasma", "polygon",
    "robinhood", "sei", "solana", "sonic",
}
ALLOWED_TIMEFRAMES = {"1", "7", "30", "90", "180"}
ALLOWED_LABELS = {"Fund", "Smart Trader", "30D Smart Trader", "90D Smart Trader", "180D Smart Trader", "Smart HL Perps Trader"}
ALLOWED_SORT_FIELDS = {
    "address", "realized_pnl_usd", "unrealized_pnl_usd", "total_pnl_usd", "avg_trade_roi",
    "roi_percent_unrealised", "win_rate", "n_trades", "n_tokens", "open_trades", "held_tokens_count",
}

chains = [c.strip() for c in CHAINS.split(",") if c.strip()]
if not chains:
    raise ValueError("chains is required")
for c in chains:
    if c not in ALLOWED_CHAINS:
        raise ValueError(f"Unsupported chain: {c!r}")
if TIMEFRAME not in ALLOWED_TIMEFRAMES:
    raise ValueError(f"Unsupported timeframe: {TIMEFRAME!r}")
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

body = {
    "chains": chains,
    "timeframe": int(TIMEFRAME),
    "pagination": {"page": 1, "per_page": int(PER_PAGE)},
    "order_by": [{"field": SORT_FIELD, "direction": SORT_DIRECTION}],
}
if labels:
    body["filters"] = {"include_smart_money_labels": labels}

response = requests.post(
    "https://api.nansen.ai/api/v1/smart-money/pnl-leaderboard",
    json=body,
    headers={"apikey": os.environ["NANSEN_API_KEY"], "Content-Type": "application/json"},
    timeout=30,
)
response.raise_for_status()

{{__df_name}} = pd.DataFrame(response.json().get("data", []))

# Raw total_pnl_usd rewards whoever traded the most, regardless of sample
# size; dividing by n_trades controls for that, and flagging big PnL built on
# very few trades surfaces the "may just be a lucky streak" risk a ranked
# PnL column alone doesn't show.
if not {{__df_name}}.empty:
    {{__df_name}}["pnl_per_trade_usd"] = (
        {{__df_name}}["total_pnl_usd"] / {{__df_name}}["n_trades"].replace(0, pd.NA)
    )
    pnl_p75 = {{__df_name}}["total_pnl_usd"].quantile(0.75)
    {{__df_name}} = {{__df_name}}.sort_values("total_pnl_usd", ascending=False, na_position="last").reset_index(drop=True)

    df = {{__df_name}}
    win = df["win_rate"] * 100 if df["win_rate"].max() <= 1 else df["win_rate"]
    df["win_rate_pct"] = win
    banked = df["realized_pnl_usd"].abs()
    paper = df["unrealized_pnl_usd"].abs()
    df["realized_share"] = banked / (banked + paper).replace(0, pd.NA)
    PROVEN_TRADES = 20
    df["small_sample_outlier"] = (df["total_pnl_usd"] >= pnl_p75) & (df["n_trades"] < PROVEN_TRADES)
    df["proven_track_record"] = (df["n_trades"] >= PROVEN_TRADES) & (win >= 50) & (df["total_pnl_usd"] > 0)
    short = df["address"].map(lambda a: f"{a[:6]}…{a[-4:]}")
    df["trader"] = (df["address_label"].map(lambda l: f"{l} · " if isinstance(l, str) and l else "") + short).astype(str)

    profit = df["total_pnl_usd"].clip(lower=0)
    top3_share = profit.head(3).sum() / profit.sum() if profit.sum() else 0.0
    paper_profit = df["unrealized_pnl_usd"].clip(lower=0).sum()
    banked_profit = df["realized_pnl_usd"].clip(lower=0).sum()
    paper_share = paper_profit / (paper_profit + banked_profit) if (paper_profit + banked_profit) else 0.0
    proven = df[df["proven_track_record"]]
    lucky = df[df["small_sample_outlier"]]

    findings = [
        f"The top 3 traders earned {top3_share:.0%} of all the profit on this leaderboard, "
        f"led by {escape(df.iloc[0]['trader'])} at ${df.iloc[0]['total_pnl_usd']:,.0f}.",
        f"{paper_share:.0%} of the profit shown is still unrealized, so it is an open bet rather than banked gains.",
    ]
    if len(proven):
        best = proven.sort_values("pnl_per_trade_usd", ascending=False).iloc[0]
        findings.append(
            f"{len(proven)} of {len(df)} traders combine {PROVEN_TRADES}+ trades, a 50%+ win rate and positive PnL. "
            f"The most efficient is {escape(best['trader'])}: ${best['pnl_per_trade_usd']:,.0f} per trade over {int(best['n_trades'])} trades."
        )
    else:
        findings.append(f"No trader here combines {PROVEN_TRADES}+ trades, a 50%+ win rate and positive PnL.")
    if len(lucky):
        findings.append(
            f"{len(lucky)} top earners made their money on fewer than {PROVEN_TRADES} trades ({escape(', '.join(lucky['trader'].head(3)))}), "
            "which could be luck rather than skill."
        )

    show(
        kpi_row([
            ("Traders analysed", len(df)),
            ("Profit from top 3", f"{top3_share:.0%}", "neg" if top3_share > 0.5 else ""),
            ("Profit still unrealized", f"{paper_share:.0%}", "neg" if paper_share > 0.5 else ""),
            ("Proven track records", len(proven), "pos"),
        ]),
        card("<ul>" + "".join(f"<li>{f}</li>" for f in findings) + "</ul>", "What stands out"),
        note(f"Proven means {PROVEN_TRADES}+ trades, a 50%+ win rate and positive PnL. Bubble size is total PnL; colour is the share of PnL already realized."),
    )

    import plotly.graph_objects as go

    plot = df.dropna(subset=["n_trades", "win_rate_pct", "total_pnl_usd"]).copy()
    plot = plot[plot["n_trades"] > 0]
    plot["size"] = plot["total_pnl_usd"].abs()
    scale = 50 / max(plot["size"].max(), 1) ** 0.5 if len(plot) else 1
    fig = go.Figure(go.Scatter(
        x=plot["n_trades"], y=plot["win_rate_pct"], mode="markers",
        marker=dict(
            size=(plot["size"] ** 0.5 * scale).clip(lower=6), color=plot["realized_share"].astype(float),
            colorscale="Viridis", cmin=0, cmax=1, showscale=True, colorbar=dict(title="Realized share"),
            line=dict(width=1, color=plot["proven_track_record"].map({True: "#16a34a", False: "rgba(0,0,0,0.25)"})),
        ),
        text=plot["trader"], customdata=plot[["total_pnl_usd", "pnl_per_trade_usd"]].astype(float),
        hovertemplate="%{text}<br>%{x} trades, %{y:.0f}% win rate<br>PnL $%{customdata[0]:,.0f} ($%{customdata[1]:,.0f}/trade)<extra></extra>",
    ))
    fig.add_vline(x=PROVEN_TRADES, line_dash="dot", opacity=0.5)
    fig.add_hline(y=50, line_dash="dot", opacity=0.5)
    fig.add_annotation(x=0.98, y=0.98, xref="paper", yref="paper", text="Proven: many trades, high win rate", showarrow=False, xanchor="right")
    fig.add_annotation(x=0.02, y=0.98, xref="paper", yref="paper", text="Possible luck: high win rate, few trades", showarrow=False, xanchor="left")
    fig.update_xaxes(type="log", title="Number of trades (log scale)")
    fig.update_yaxes(title="Win rate (%)")
    fig.update_layout(title="Who is actually good? Smart money by track record (green ring = proven)")
    fig.show()
else:
    show(note("No smart-money PnL data matched these filters."))
