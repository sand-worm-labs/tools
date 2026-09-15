# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
FROM_ADDRESS = "{{from_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not ADDRESS_RE.match(FROM_ADDRESS):
    raise ValueError(f"Invalid from_address: {FROM_ADDRESS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
from_hex_addr = FROM_ADDRESS[2:].lower()

sql = f"""
with withdrawals as (
    select "to" as wallet, date_trunc('day', block_time) as day
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "from" = from_hex('{from_hex_addr}')
),
first_withdrawal as (
    select wallet, min(day) as first_day
    from withdrawals
    group by wallet
)
select
    first_day as day,
    count(*) as unique_withdrawers
from first_withdrawal
group by first_day
order by first_day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
