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
with received as (
    select "to" as address, block_date, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "to" <> from_hex('{zero_hex}')
),
sent as (
    select "from" as address, block_date, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "from" <> from_hex('{zero_hex}')
),
movements as (
    select * from received
    union all
    select * from sent
),
first_seen as (
    select address, min(block_date) as first_date
    from received
    group by address
),
balances as (
    select address, sum(amt) as balance
    from movements
    group by address
)
select
    to_hex(f.address) as address,
    f.first_date,
    b.balance
from first_seen f
join balances b on b.address = f.address
where b.balance > 0
order by f.first_date
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
