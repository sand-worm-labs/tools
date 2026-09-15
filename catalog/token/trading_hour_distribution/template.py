# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
select
    lpad(cast(hour(block_time) as varchar), 2, '0') || ':' || lpad(cast(minute(block_time) as varchar), 2, '0') as hour_minute,
    count(*) as trades_count,
    count(distinct date_trunc('day', block_time)) as days_active
from dex.trades
where blockchain = '{CHAIN}'
  and (token_bought_address = from_hex('{contract_hex}') or token_sold_address = from_hex('{contract_hex}'))
group by 1
order by trades_count desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
