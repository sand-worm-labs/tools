# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not DAYS.isdigit() or int(DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {DAYS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with interactions as (
    select "from" as user_address, date_trunc('day', block_time) as day
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and "to" = from_hex('{contract_hex}')
      and block_time >= now() - interval '{DAYS}' day
    group by 1, 2
),
first_seen as (
    select user_address, min(day) as cohort_start
    from interactions
    group by user_address
),
cohorts as (
    select
        f.user_address,
        date_trunc('week', f.cohort_start) as cohort_week,
        i.day,
        date_diff('day', f.cohort_start, i.day) as day_offset
    from interactions i
    join first_seen f on f.user_address = i.user_address
),
cohort_sizes as (
    select cohort_week, count(distinct user_address) as cohort_size
    from cohorts
    where day_offset = 0
    group by cohort_week
)
select
    c.cohort_week,
    d.retention_day,
    count(distinct case when c.day_offset = d.retention_day then c.user_address end) as active_users,
    count(distinct case when c.day_offset = d.retention_day then c.user_address end) * 1.0 / nullif(s.cohort_size, 0) as retention_rate
from cohorts c
join cohort_sizes s on s.cohort_week = c.cohort_week
cross join (values (0), (7), (14), (21), (28)) as d(retention_day)
group by c.cohort_week, d.retention_day, s.cohort_size
order by c.cohort_week, d.retention_day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
