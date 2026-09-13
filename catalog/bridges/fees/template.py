# Sandworm Power Toolbox — {{__tool_name}}
PROTOCOL = "{{protocol}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
# Only Hop and the native Optimism bridge have fee data available in this
# catalog's verified tables. Across/Synapse/Stargate expose deposit/withdrawal
# amounts but not a decomposed protocol+relayer fee split, and native
# Arbitrum/Base bridges don't charge a protocol fee (only L1 gas).
SUPPORTED_PROTOCOLS = {"hop", "optimism_bridge"}

if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")
if PROTOCOL not in SUPPORTED_PROTOCOLS:
    raise ValueError(
        f"bridges.fees only has verified fee data for: {sorted(SUPPORTED_PROTOCOLS)}. "
        f"{PROTOCOL!r} either doesn't charge a decomposable protocol fee, or no verified fee "
        f"breakdown exists in this catalog's data sources yet."
    )

limit_clause = f"limit {LIMIT}" if LIMIT else ""

if PROTOCOL == "hop":
    time_where = "" if DAYS == "all" else f"and block_time >= now() - interval '{DAYS}' day"
    sql = f"""
    select
        date_trunc('day', block_time) as day,
        sum(fee_amount_usd) as total_fees_usd,
        sum(token_amount_usd) as volume_usd,
        sum(fee_amount_usd) / nullif(sum(token_amount_usd), 0) * 100 as effective_fee_pct
    from hop_protocol.flows
    where 1 = 1 {time_where}
    group by 1
    order by 1 desc
    {limit_clause}
    """
else:  # optimism_bridge — native bridge charges no protocol fee, only L1 gas (not modeled here)
    time_where = "" if DAYS == "all" else f"and block_time >= now() - interval '{DAYS}' day"
    sql = f"""
    select
        date_trunc('day', block_time) as day,
        sum(fee_amount_usd) as total_fees_usd,
        sum(token_amount_usd) as volume_usd,
        0.0 as effective_fee_pct
    from bridge_optimism.standard_bridge_flows
    where 1 = 1 {time_where}
    group by 1
    order by 1 desc
    {limit_clause}
    """

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="day", y="effective_fee_pct")
fig.show()

{{__df_name}}
