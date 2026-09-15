# Sandworm Power Toolbox — {{__tool_name}}
# No `contract_address` existed on this tool originally; added since a
# "most recent token balance" ranking is meaningless without picking a token.
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if LOOKBACK_DAYS and not (LOOKBACK_DAYS.isdigit() and int(LOOKBACK_DAYS) > 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
lookback_val = int(LOOKBACK_DAYS) if LOOKBACK_DAYS else 30

# Balance uses full transfer history (a partial-window balance would not be
# an actual balance); lookback_days instead selects which wallets count as
# "recent" holders (i.e. active within the window), matching the tool's
# "most recent" framing.
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
recent_activity as (
    select distinct address
    from all_movements
    where block_time >= now() - interval '{lookback_val}' day
)
select
    to_hex(b.address) as owner,
    b.balance as token_balance
from balances b
join recent_activity r on r.address = b.address
order by b.balance desc
limit 500
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
