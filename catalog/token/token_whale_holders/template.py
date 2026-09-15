# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
MIN_BALANCE = "{{min_balance}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
try:
    min_balance_val = float(MIN_BALANCE)
except ValueError:
    raise ValueError(f"Invalid min_balance: {MIN_BALANCE!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with movements as (
    select "to" as address, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
    union all
    select "from" as address, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
),
balances as (
    select address, sum(amt) as balance
    from movements
    group by address
)
select
    count(*) as whale_count,
    '{MIN_BALANCE}' as threshold
from balances
where balance >= {min_balance_val}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
