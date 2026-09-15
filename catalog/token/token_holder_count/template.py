# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
zero_hex = "0" * 40

sql = f"""
with movements as (
    select "to" as address, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "to" <> from_hex('{zero_hex}')
    union all
    select "from" as address, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "from" <> from_hex('{zero_hex}')
),
balances as (
    select address, sum(amt) as balance
    from movements
    group by address
)
select count(*) as holder_count
from balances
where balance > 0
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
