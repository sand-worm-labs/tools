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
    having sum(amt) > 0
),
stats as (
    select count(*) as n, sum(balance) as total_balance, max(balance) as max_balance
    from balances
),
ranked as (
    select balance, row_number() over (order by balance) as rn
    from balances
)
select
    sum((2 * r.rn - s.n - 1) * r.balance) / (s.n * s.total_balance) as gini,
    s.n as holders,
    s.max_balance / s.total_balance as top_holder_pct
from ranked r
cross join stats s
group by s.n, s.total_balance, s.max_balance
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
