# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
CLAIMER_ADDRESSES_RAW = "{{claimer_addresses}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

# claimer_addresses arrives as a comma-separated string of 0x addresses.
claimer_addresses = [a.strip() for a in CLAIMER_ADDRESSES_RAW.strip("[] ").split(",") if a.strip()]
if not claimer_addresses:
    raise ValueError("claimer_addresses must contain at least one address")
for a in claimer_addresses:
    if not ADDRESS_RE.match(a):
        raise ValueError(f"Invalid address in claimer_addresses: {a!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
claimer_hex_list = ", ".join(f"from_hex('{a[2:].lower()}')" for a in claimer_addresses)

sql = f"""
select
    date_trunc('week', block_time) as week,
    sum(amount_usd) as sales,
    count(distinct taker) as recipients
from dex.trades
where blockchain = '{CHAIN}'
  and token_sold_address = from_hex('{contract_hex}')
  and taker in ({claimer_hex_list})
group by 1
order by 1
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
