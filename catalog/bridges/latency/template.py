# Sandworm Power Toolbox — {{__tool_name}}
PROTOCOL = "{{protocol}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
# Latency needs a deposit row and its matching withdrawal row joined by a
# shared transfer id — only available for protocols with both sides modeled.
# Hop/Optimism Bridge (see fees/tvl) represent each transfer as a single
# pre-joined row with no separate source/destination timestamps to diff.
SUPPORTED_PROTOCOLS = {"across", "synapse", "arbitrum_bridge"}

# (chain, deposits table, withdrawals table) triples — curated, individually
# verified subset; see volume/template.py for the same caveat.
PROTOCOL_TABLES = {
    "across": [
        ("ethereum", "across_v3_deposits", "across_v3_withdrawals"),
        ("optimism", "across_v3_deposits", "across_v3_withdrawals"),
        ("arbitrum", "across_v3_deposits", "across_v3_withdrawals"),
        ("base", "across_v3_deposits", "across_v3_withdrawals"),
        ("polygon", "across_v3_deposits", "across_v3_withdrawals"),
        ("bnb", "across_v3_deposits", "across_v3_withdrawals"),
    ],
    "synapse": [
        ("ethereum", "synapse_rfq_deposits", "synapse_rfq_withdrawals"),
        ("optimism", "synapse_rfq_deposits", "synapse_rfq_withdrawals"),
        ("arbitrum", "synapse_rfq_deposits", "synapse_rfq_withdrawals"),
        ("base", "synapse_rfq_deposits", "synapse_rfq_withdrawals"),
        ("bnb", "synapse_rfq_deposits", "synapse_rfq_withdrawals"),
    ],
    "arbitrum_bridge": [
        ("ethereum", "arbitrum_native_v1_deposits", "arbitrum_native_v1_withdrawals"),
    ],
}

if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")
if PROTOCOL not in SUPPORTED_PROTOCOLS:
    raise ValueError(
        f"bridges.latency only has verified deposit+withdrawal pairs for: {sorted(SUPPORTED_PROTOCOLS)}. "
        f"{PROTOCOL!r} either has no matching withdrawal-side table in this catalog, or represents "
        f"transfers as a single pre-joined row with nothing to diff."
    )

limit_clause = f"limit {LIMIT}" if LIMIT else ""

time_where = "" if DAYS == "all" else f"and d.block_time >= now() - interval '{DAYS}' day"

union_parts = [
    f"""select
        d.block_time as deposit_time,
        w.block_time as withdrawal_time,
        d.deposit_chain as source_chain,
        d.withdrawal_chain as dest_chain
    from bridges_{chain}.{dep_t} d
    join bridges_{chain}.{wd_t} w on w.bridge_transfer_id = d.bridge_transfer_id
    where 1 = 1 {time_where}
    """
    for chain, dep_t, wd_t in PROTOCOL_TABLES[PROTOCOL]
]
union_sql = "\nunion all\n".join(union_parts)

sql = f"""
with matched as (
    {union_sql}
)
select
    source_chain,
    dest_chain,
    avg(date_diff('second', deposit_time, withdrawal_time)) as avg_latency_seconds,
    approx_percentile(date_diff('second', deposit_time, withdrawal_time), 0.5) as median_latency_seconds,
    approx_percentile(date_diff('second', deposit_time, withdrawal_time), 0.9) as p90_latency_seconds,
    count(*) as transfer_count
from matched
where withdrawal_time > deposit_time
group by 1, 2
order by transfer_count desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="source_chain", y="median_latency_seconds", color="dest_chain")
fig.show()

{{__df_name}}
