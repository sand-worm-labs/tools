# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
WALLET = "{{wallet}}"
DAYS = "{{days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_DAYS = {"7", "30", "90", "180", "365", "all"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(WALLET):
    raise ValueError(f"Invalid wallet: {WALLET!r}")
if DAYS not in ALLOWED_DAYS:
    raise ValueError(f"Unsupported days range: {DAYS!r}")

sql = f"""
select
    date_trunc('day', block_time) as day,
    count(*) as tx_count,
    sum(gas_used) as total_gas_used,
    avg(gas_price) / 1e9 as avg_gas_price_gwei,
    sum(gas_used * gas_price) / 1e18 as total_fees_eth
from {CHAIN}.transactions
where "from" = from_hex('{WALLET[2:].lower()}')
  {{__time_where}}
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
