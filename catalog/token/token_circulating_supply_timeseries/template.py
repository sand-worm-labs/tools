# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}".strip()
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

# Full daily history (see token_circulating_supply for a single latest
# snapshot): cumulative sum of daily net mint/burn gives the day-by-day
# circulating supply curve.
sql = f"""
with movements as (
    select
        block_date as day,
        case
            when "from" = from_hex('0000000000000000000000000000000000000000') then amount
            when "to" = from_hex('0000000000000000000000000000000000000000') then -amount
            else 0
        end as net_amount
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and (
        "from" = from_hex('0000000000000000000000000000000000000000')
        or "to" = from_hex('0000000000000000000000000000000000000000')
      )
),
daily as (
    select day, sum(net_amount) as net_change
    from movements
    group by day
)
select
    day,
    sum(net_change) over (order by day) as supply
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
