# Sandworm Power Toolbox — {{__tool_name}}
# Distinguished from token.top_holders (plain all-time balance rank): this
# tool restricts to wallets with on-chain activity in the last 180 days,
# matching its "most recent activity" framing.
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
TOP_N = "{{top_n}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
RECENT_ACTIVITY_DAYS = 180

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if TOP_N and not (TOP_N.isdigit() and int(TOP_N) > 0):
    raise ValueError(f"Invalid top_n: {TOP_N!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
top_n_val = int(TOP_N) if TOP_N else 100

sql = f"""
with all_movements as (
    select "to" as address, amount as amt, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
    union all
    select "from" as address, -amount as amt, block_time
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
),
balances as (
    select address, sum(amt) as balance
    from all_movements
    group by address
    having sum(amt) > 0
),
active_wallets as (
    select distinct address
    from all_movements
    where block_time >= now() - interval '{RECENT_ACTIVITY_DAYS}' day
)
select
    row_number() over (order by b.balance desc) as rank,
    to_hex(b.address) as address,
    b.balance as balance
from balances b
join active_wallets a on a.address = b.address
order by b.balance desc
limit {top_n_val}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
