# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
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
ZERO_ADDRESS = "0000000000000000000000000000000000000000"

sql = f"""
with movements as (
    select
        date_trunc('{INTERVAL}', block_time) as day,
        case when "from" = from_hex('{ZERO_ADDRESS}') then amount else 0 end as minted,
        case when "to" = from_hex('{ZERO_ADDRESS}') then amount else 0 end as burned
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and ("from" = from_hex('{ZERO_ADDRESS}') or "to" = from_hex('{ZERO_ADDRESS}'))
),
bucketed as (
    select day, sum(minted) as minted, sum(burned) as burned
    from movements
    group by day
)
select
    day,
    minted,
    burned,
    sum(minted - burned) over (order by day) as supply
from bucketed
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
