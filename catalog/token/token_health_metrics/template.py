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

token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with trades as (
    select
        block_time,
        taker,
        amount_usd,
        case when token_bought_address = from_hex('{token_hex}') then amount_usd else 0 end as buy_usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{token_hex}') or token_sold_address = from_hex('{token_hex}'))
      and block_time >= now() - interval '30' day
)
select
    count(distinct taker) as unique_traders,
    sum(amount_usd) as total_volume_usd,
    sum(buy_usd) / nullif(sum(amount_usd), 0) as buy_pressure,
    sum(amount_usd) filter (where block_time >= now() - interval '1' day) as today_volume
from trades
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
