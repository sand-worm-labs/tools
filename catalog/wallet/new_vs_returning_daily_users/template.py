# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DAYS.isdigit() or int(DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {DAYS!r}")

sql = f"""
with first_tx as (
    select "from" as address, min(date_trunc('day', block_time)) as first_day
    from tokens.transfers
    where blockchain = '{CHAIN}'
    group by "from"
),
daily_activity as (
    select date_trunc('day', block_time) as day, "from" as address
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{DAYS}' day
    group by 1, 2
)
select
    d.day as date,
    count(*) filter (where f.first_day = d.day) as new_users,
    count(*) as total_active_users
from daily_activity d
join first_tx f on f.address = d.address
group by d.day
order by d.day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
