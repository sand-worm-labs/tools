# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
TOP_N = "{{top_n}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if TOP_N and not (TOP_N.isdigit() and int(TOP_N) > 0):
    raise ValueError(f"Invalid top_n: {TOP_N!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
top_n_val = int(TOP_N) if TOP_N else 10

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
),
top_wallets as (
    select address
    from balances
    order by balance desc
    limit {top_n_val}
),
monthly as (
    select date_trunc('month', t.block_time) as month, t."to" as wallet, t.amount as received, 0 as sent
    from tokens.transfers t
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.contract_address = from_hex('{contract_hex}')
      and t."to" in (select address from top_wallets)
    union all
    select date_trunc('month', t.block_time) as month, t."from" as wallet, 0 as received, t.amount as sent
    from tokens.transfers t
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.contract_address = from_hex('{contract_hex}')
      and t."from" in (select address from top_wallets)
)
select
    month,
    to_hex(wallet) as holder,
    sum(sent) as sent,
    sum(received) as received
from monthly
group by 1, 2
order by month desc, received desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
