# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
INTERVAL = "{{interval}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_INTERVALS = {"minute", "hour", "day", "week", "month"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if INTERVAL not in ALLOWED_INTERVALS:
    raise ValueError(f"Unsupported interval: {INTERVAL!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with first_seen as (
    select "to" as wallet, min(block_time) as first_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
    group by "to"
)
select
    cast(date_trunc('{INTERVAL}', first_time) as varchar) as period,
    count(*) as new_holders
from first_seen
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
