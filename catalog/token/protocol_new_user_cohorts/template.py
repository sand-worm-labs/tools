# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
PROTOCOL_ADDRESS = "{{protocol_address}}"
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CHAIN_SCHEMA = {
    "ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum",
    "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche_c", "celo": "celo",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(PROTOCOL_ADDRESS):
    raise ValueError(f"Invalid protocol_address: {PROTOCOL_ADDRESS!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

schema = CHAIN_SCHEMA[CHAIN]
protocol_hex = PROTOCOL_ADDRESS[2:].lower()

sql = f"""
with first_seen as (
    select "from" as user, min(block_time) as first_time
    from {schema}.transactions
    where "to" = from_hex('{protocol_hex}')
      and success = true
      and block_time >= date '{DATE_FROM}'
    group by 1
),
daily as (
    select date_trunc('day', first_time) as first_time, count(*) as new_users
    from first_seen
    group by 1
)
select
    first_time,
    new_users,
    sum(new_users) over (order by first_time) as cumulative_users
from daily
order by first_time
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
