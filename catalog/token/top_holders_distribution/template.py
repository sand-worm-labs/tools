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
top_n_val = int(TOP_N) if TOP_N else 100

# "share" is each holder's fraction of the sum of all positive holder
# balances (a proxy for circulating supply held by tracked addresses, since
# burn/mint totals aren't reliably derivable from transfers alone).
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
    having sum(amt) > 0
),
totals as (
    select sum(balance) as total_balance from balances
)
select
    to_hex(b.address) as address,
    b.balance,
    b.balance / nullif(t.total_balance, 0) as share,
    row_number() over (order by b.balance desc) as rank
from balances b
cross join totals t
order by b.balance desc
limit {top_n_val}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
