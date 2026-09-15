# Sandworm Power Toolbox — {{__tool_name}}
import re
from datetime import datetime

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
BURN_ADDRESSES_RAW = '''{{burn_addresses}}'''.replace("[", "").replace("]", "").replace('"', "")
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
try:
    datetime.strptime(DATE_FROM, "%Y-%m-%d")
except ValueError:
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

burn_addresses = [a.strip() for a in BURN_ADDRESSES_RAW.split(",") if a.strip()]
if not burn_addresses:
    burn_addresses = ["0x0000000000000000000000000000000000000000", "0x000000000000000000000000000000000000dEaD"]
for a in burn_addresses:
    if not ADDRESS_RE.match(a):
        raise ValueError(f"Invalid burn_addresses entry: {a!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
burn_hex_list = ", ".join(f"from_hex('{a[2:].lower()}')" for a in burn_addresses)

sql = f"""
with daily_burns as (
    select date_trunc('day', block_time) as day, sum(amount) as total_burn
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and "to" in ({burn_hex_list})
      and block_time >= date '{DATE_FROM}'
    group by day
)
select
    day,
    total_burn,
    avg(total_burn) over (order by day rows between 45 preceding and current row) as ma46,
    avg(total_burn) over (order by day rows between 199 preceding and current row) as ma200
from daily_burns
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
