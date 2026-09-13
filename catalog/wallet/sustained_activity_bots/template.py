# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}"
THRESHOLD_HOURS = "{{threshold_hours}}"

CHAIN_SCHEMA = {
    "ethereum": "ethereum",
    "base": "base",
    "optimism": "optimism",
    "arbitrum": "arbitrum",
    "polygon": "polygon",
    "bsc": "bnb",
    "avalanche": "avalanche_c",
    "celo": "celo",
}
ALLOWED_CHAINS = set(CHAIN_SCHEMA)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
if not THRESHOLD_HOURS.isdigit() or not (0 < int(THRESHOLD_HOURS) <= 24):
    raise ValueError(f"Invalid threshold_hours: {THRESHOLD_HOURS!r}")

schema = CHAIN_SCHEMA[CHAIN]

sql = f"""
with hourly as (
    select
        "from" as address,
        date_trunc('day', block_time) as day,
        count(distinct date_trunc('hour', block_time)) as active_hours
    from {schema}.transactions
    where success
      and block_time >= date '{DATE_FROM}'
    group by 1, 2
),
qualifying_days as (
    select address, day, active_hours
    from hourly
    where active_hours >= {THRESHOLD_HOURS}
)
select
    to_hex(address) as address,
    avg(active_hours) as active_hours,
    avg(active_hours) / 24.0 as bot_score
from qualifying_days
group by 1
order by bot_score desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
