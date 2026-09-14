# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DATE_FROM = "{{date_from}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with daily_mint_burn as (
    select
        date_trunc('day', block_time) as day,
        sum(case when "from" = from_hex('0000000000000000000000000000000000000000') then amount else 0 end) as minted,
        sum(case when "to" in (from_hex('0000000000000000000000000000000000000000'), from_hex('000000000000000000000000000000000000dead')) then amount else 0 end) as burned
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and block_time >= timestamp '{DATE_FROM}'
    group by 1
)
select
    day,
    sum(minted - burned) over (order by day) as circulating_supply
from daily_mint_burn
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
