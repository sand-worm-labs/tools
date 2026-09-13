# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET_ADDRESS = "{{wallet_address}}"
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET_ADDRESS):
    raise ValueError(f"Invalid wallet_address: {WALLET_ADDRESS!r}")

schema = CHAIN_SCHEMA[CHAIN]
wallet_hex = WALLET_ADDRESS[2:].lower()
# "SOL volume" in the original description is generalized here to native-token
# inflow volume across supported EVM chains (this catalog is EVM-only).
date_from_clause = f"and block_time >= date('{DATE_FROM}')" if DATE_RE.match(DATE_FROM) else "and block_time >= now() - interval '365' day"

sql = f"""
select
    cast(date_trunc('day', block_time) as date) as day,
    count(*) as daily_in_txs,
    sum(value) / 1e18 as daily_in_native
from {schema}.transactions
where "to" = from_hex('{wallet_hex}')
  and value > 0
  {date_from_clause}
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
