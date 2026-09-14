# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if DATE_FROM and not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
zero_hex = "0" * 40
date_filter = f"where day >= date '{DATE_FROM}'" if DATE_FROM else ""

sql = f"""
with movements as (
    select date_trunc('day', block_time) as day, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "from" = from_hex('{zero_hex}')
    union all
    select date_trunc('day', block_time) as day, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "to" = from_hex('{zero_hex}')
),
daily as (
    select day, sum(amt) as daily_change
    from movements
    group by day
),
cumulative as (
    select day, daily_change, sum(daily_change) over (order by day) as total_supply
    from daily
)
select day, daily_change, total_supply
from cumulative
{date_filter}
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
