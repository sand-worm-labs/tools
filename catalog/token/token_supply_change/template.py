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

contract_hex = CONTRACT_ADDRESS[2:].lower()
date_where = f"and block_time >= timestamp '{DATE_FROM}'" if DATE_FROM else ""
ZERO_ADDRESS = "0000000000000000000000000000000000000000"

# EVM equivalent of mint/burn detection: an ERC20 Transfer with from == the
# zero address is a mint, and to == the zero address is a burn.
sql = f"""
with movements as (
    select
        date_trunc('day', block_time) as day,
        case when "from" = from_hex('{ZERO_ADDRESS}') then amount else 0 end as minted,
        case when "to" = from_hex('{ZERO_ADDRESS}') then amount else 0 end as burned
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and ("from" = from_hex('{ZERO_ADDRESS}') or "to" = from_hex('{ZERO_ADDRESS}'))
      {date_where}
),
daily as (
    select day, sum(minted) as daily_minted, sum(burned) as daily_burned
    from movements
    group by day
)
select
    day,
    daily_minted,
    daily_burned,
    sum(daily_minted - daily_burned) over (order by day) as cumulative_supply
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
