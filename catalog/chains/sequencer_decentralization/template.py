# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
DAYS = "{{days}}"
LIMIT = "{{limit}}".strip()

ALLOWED_CHAINS = {"base", "optimism", "arbitrum", "polygon", "scroll", "linea", "zksync"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
# A gap between consecutive blocks wider than this is treated as a candidate
# sequencer downtime event.
DOWNTIME_GAP_SECONDS = 30

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")
if LIMIT and not (LIMIT.isdigit() and int(LIMIT) > 0):
    raise ValueError(f"Invalid limit: {LIMIT!r}")

time_where = "" if DAYS == "all" else f"AND time >= NOW() - INTERVAL '{DAYS}' DAY"
limit_clause = f"limit {LIMIT}" if LIMIT else ""

# Forced-inclusion transactions and validator/sequencer-set membership
# aren't exposed as a stable, chain-agnostic Dune table across L2 stacks, so
# this uses block-to-block time gaps as an observable proxy: a single
# centralized sequencer producing blocks on a fixed cadence shows tight,
# regular gaps, while wide/irregular gaps are a candidate downtime signal.
sql = f"""
with block_gaps as (
    select
        time,
        number,
        date_diff('second', lag(time) over (order by number), time) as gap_seconds
    from {CHAIN}.blocks
    where 1 = 1
      {time_where}
)
select
    date_trunc('day', time) as day,
    count(*) as block_count,
    avg(gap_seconds) as avg_block_gap_seconds,
    max(gap_seconds) as max_block_gap_seconds,
    count_if(gap_seconds > {DOWNTIME_GAP_SECONDS}) as downtime_events
from block_gaps
group by 1
order by 1 desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="day", y="downtime_events")
fig.show()

{{__df_name}}
