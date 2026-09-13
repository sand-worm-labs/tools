# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}"

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
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

schema = CHAIN_SCHEMA[CHAIN]
contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with daily as (
    select
        date_trunc('day', block_time) as day,
        count(distinct "from") as daily_active_users
    from {schema}.transactions
    where "to" = from_hex('{contract_hex}')
      and success
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
)
select
    day,
    daily_active_users,
    avg(daily_active_users) over (order by day rows between 6 preceding and current row) as avg_dau_7d
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
