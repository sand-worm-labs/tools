# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with trades as (
    select taker as trader, amount_usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{contract_hex}') or token_sold_address = from_hex('{contract_hex}'))
),
agg as (
    select trader, avg(amount_usd) as avg_usd_vol
    from trades
    group by 1
)
select
    to_hex(trader) as trader_id,
    case
        when avg_usd_vol >= 100000 then 'whale'
        when avg_usd_vol >= 10000 then 'dolphin'
        when avg_usd_vol >= 1000 then 'fish'
        else 'shrimp'
    end as classification,
    avg_usd_vol
from agg
order by avg_usd_vol desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
