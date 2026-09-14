# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
TOP_N = "{{top_n}}".strip()
MIN_BALANCE = "{{min_balance}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if TOP_N and not TOP_N.isdigit():
    raise ValueError(f"Invalid top_n: {TOP_N!r}")
try:
    min_balance_val = float(MIN_BALANCE) if MIN_BALANCE else 0.0
except ValueError:
    raise ValueError(f"Invalid min_balance: {MIN_BALANCE!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
top_n_val = int(TOP_N) if TOP_N else 100
# tokens.transfers.amount is already decimal-adjusted (human units), not raw
# wei, so min_balance is applied in token units despite its wei-labeled name.

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
    having sum(amt) >= {min_balance_val}
)
select
    to_hex(address) as address,
    balance,
    row_number() over (order by balance desc) as rank
from balances
order by balance desc
limit {top_n_val}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
