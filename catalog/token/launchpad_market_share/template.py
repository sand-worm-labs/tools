# Sandworm Power Toolbox — {{__tool_name}}
# EVM generalization: "pump.fun vs total launches" (Solana-only) reinterpreted as
# one EVM launchpad factory's share of all new ERC-20 token contracts on the chain.
import json
import re

CHAIN = "{{chain}}"
FACTORY_ADDRESS = "{{factory_address}}"
DATE_RANGE = json.loads('''{{date_range}}''')

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(FACTORY_ADDRESS):
    raise ValueError(f"Invalid factory_address: {FACTORY_ADDRESS!r}")

date_from = DATE_RANGE.get("from", "")
date_to = DATE_RANGE.get("to", "")
if not DATE_RE.match(date_from) or not DATE_RE.match(date_to):
    raise ValueError(f"Invalid date_range: {DATE_RANGE!r}")

schema = CHAIN_SCHEMA[CHAIN]
factory_hex = FACTORY_ADDRESS[2:].lower()

sql = f"""
with creations as (
    select date_trunc('day', block_time) as day, address as token_address, deployer
    from {schema}.creation_traces
    where block_time >= date '{date_from}'
      and block_time < date '{date_to}' + interval '1' day
),
daily as (
    select
        day,
        count(distinct case when deployer = from_hex('{factory_hex}') then token_address end) as factory_launches,
        count(distinct token_address) as total_launches
    from creations
    group by 1
)
select
    day as date,
    factory_launches,
    total_launches,
    factory_launches * 1.0 / nullif(total_launches, 0) as factory_share
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
