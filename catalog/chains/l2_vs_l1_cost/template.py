# Sandworm Power Toolbox — {{__tool_name}}
L2_CHAIN = "{{l2_chain}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"base", "optimism", "arbitrum", "polygon", "scroll", "linea", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}

if L2_CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported l2_chain: {L2_CHAIN!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

time_where = "" if DAYS == "all" else f"AND block_time >= NOW() - INTERVAL '{DAYS}' DAY"
limit_clause = f"limit {LIMIT}" if LIMIT else ""

# Compares the average fee of *all* transactions on each chain, not a
# normalized like-for-like transfer — a fair proxy at this grain since both
# sides mix the same broad mix of simple transfers and contract calls.
sql = f"""
with l2_costs as (
    select date_trunc('day', block_time) as day, avg(gas_used * gas_price) / 1e18 as avg_l2_fee_eth
    from {L2_CHAIN}.transactions
    where 1 = 1 {time_where}
    group by 1
),
l1_costs as (
    select date_trunc('day', block_time) as day, avg(gas_used * gas_price) / 1e18 as avg_l1_fee_eth
    from ethereum.transactions
    where 1 = 1 {time_where}
    group by 1
)
select
    coalesce(l2.day, l1.day) as day,
    l2.avg_l2_fee_eth,
    l1.avg_l1_fee_eth,
    (1 - l2.avg_l2_fee_eth / nullif(l1.avg_l1_fee_eth, 0)) * 100 as pct_savings
from l2_costs l2
full outer join l1_costs l1 on l1.day = l2.day
order by day desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="day", y=["avg_l2_fee_eth", "avg_l1_fee_eth"])
fig.show()

{{__df_name}}
