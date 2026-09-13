# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
DEPLOYERS = "{{deployers}}"
INTERVAL = "{{interval}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ALLOWED_INTERVALS = {"minute", "hour", "day", "week", "month"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(DEPLOYERS):
    raise ValueError(f"Invalid deployers address: {DEPLOYERS!r}")
if INTERVAL not in ALLOWED_INTERVALS:
    raise ValueError(f"Unsupported interval: {INTERVAL!r}")

schema = CHAIN_SCHEMA[CHAIN]
deployer_hex = DEPLOYERS[2:].lower()

sql = f"""
with creations as (
    select date_trunc('{INTERVAL}', block_time) as period, count(*) as created_wallets
    from {schema}.traces
    where "from" = from_hex('{deployer_hex}')
      and type = 'create'
      and success
    group by 1
)
select
    period,
    created_wallets,
    sum(created_wallets) over (order by period) as cumulative_wallets
from creations
order by period
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
