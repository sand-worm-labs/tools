# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
PROTOCOL = "{{protocol}}".strip()
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
CHAIN_SCHEMA = {
    "ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum",
    "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche_c", "celo": "celo",
}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
# "protocol" is a free-text field, but a contract address is what the query
# needs to filter transactions, so it must still look like one.
if not ADDRESS_RE.match(PROTOCOL):
    raise ValueError(f"Invalid protocol (must be a contract address): {PROTOCOL!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

schema = CHAIN_SCHEMA[CHAIN]
protocol_hex = PROTOCOL[2:].lower()

sql = f"""
with txs as (
    select "from" as user, date_trunc('day', block_time) as day
    from {schema}.transactions
    where "to" = from_hex('{protocol_hex}')
      and success = true
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
first_seen as (
    select user, min(day) as first_day
    from txs
    group by user
),
daily_new as (
    select first_day as day, count(*) as new_users
    from first_seen
    group by 1
)
select
    day,
    new_users,
    sum(new_users) over (order by day) as cumulative_users
from daily_new
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
