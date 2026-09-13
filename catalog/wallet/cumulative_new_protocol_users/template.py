# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
PROTOCOL = "{{protocol}}"
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(PROTOCOL):
    raise ValueError(f"Invalid protocol address: {PROTOCOL!r}")
if DATE_FROM and not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

protocol_hex = PROTOCOL[2:].lower()
date_from_clause = f"and block_time >= date '{DATE_FROM}'" if DATE_FROM else ""

sql = f"""
with first_interactions as (
    select "from" as wallet, min(date_trunc('day', block_time)) as first_day
    from {CHAIN}.transactions
    where "to" = from_hex('{protocol_hex}')
      {date_from_clause}
    group by 1
),
daily_new as (
    select first_day as date, count(*) as new_users
    from first_interactions
    group by 1
)
select
    date,
    new_users,
    sum(new_users) over (order by date) as cumulative_users
from daily_new
order by date
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
