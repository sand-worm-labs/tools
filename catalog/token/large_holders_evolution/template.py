# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
MIN_BALANCE = "{{min_balance}}"
DATE_FROM = "{{date_from}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
CHAIN_SCHEMA = {"ethereum": "ethereum", "base": "base", "optimism": "optimism", "arbitrum": "arbitrum", "polygon": "polygon", "bsc": "bnb", "avalanche": "avalanche", "celo": "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
try:
    min_balance_val = float(MIN_BALANCE)
except ValueError:
    raise ValueError(f"Invalid min_balance: {MIN_BALANCE!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

schema = CHAIN_SCHEMA[CHAIN]
contract_hex = CONTRACT_ADDRESS[2:].lower()

# Running per-holder balance built from all transfers (not just those after
# date_from) so the balance on date_from itself already reflects prior
# history; date_from only bounds which rows are returned, not which rows
# feed the running sum.
sql = f"""
with movements as (
    select block_time, "to" as holder, amount as amt
    from tokens.transfers
    where blockchain = '{schema}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
    union all
    select block_time, "from" as holder, -amount as amt
    from tokens.transfers
    where blockchain = '{schema}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
),
daily as (
    select date_trunc('day', block_time) as day, holder, sum(amt) as net_change
    from movements
    group by 1, 2
),
running as (
    select
        day,
        holder,
        sum(net_change) over (partition by holder order by day) as balance
    from daily
)
select
    day as date,
    concat('0x', to_hex(holder)) as holder_address,
    balance
from running
where day >= date('{DATE_FROM}')
  and balance >= {min_balance_val}
order by day, balance desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
