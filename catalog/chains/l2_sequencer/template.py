# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"base", "optimism", "arbitrum", "polygon", "scroll", "linea", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

time_where = "" if DAYS == "all" else f"AND time >= NOW() - INTERVAL '{DAYS}' DAY"
limit_clause = f"limit {LIMIT}" if LIMIT else ""

# Actual L1 batch-submission events (batch size, compression ratio) aren't
# exposed as a stable, chain-agnostic Dune table across L2 stacks as
# different as OP-stack, Arbitrum Nitro, and zkSync/Scroll/Linea's zk
# rollups. Block production cadence and size on the L2 chain itself is used
# here as an observable proxy for sequencer batching activity instead.
sql = f"""
select
    date_trunc('hour', time) as hour,
    count(*) as block_count,
    avg(size) as avg_block_size_bytes,
    3600.0 / nullif(count(*), 0) as avg_block_interval_seconds,
    avg(gas_used) as avg_gas_used,
    avg(cast(gas_used as double) / nullif(gas_limit, 0)) as avg_gas_utilization
from {CHAIN}.blocks
where 1 = 1
  {time_where}
group by 1
order by 1 desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="hour", y="block_count")
fig.show()

{{__df_name}}
