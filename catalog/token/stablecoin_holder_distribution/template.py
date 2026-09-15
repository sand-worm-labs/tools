# Sandworm Power Toolbox — {{__tool_name}}
# Assumes the token is a USD-pegged stablecoin, so 1 unit == 1 USD for the
# threshold comparison (no separate price join needed).
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
THRESHOLD_USD = "{{threshold_usd}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not THRESHOLD_USD.replace(".", "", 1).isdigit():
    raise ValueError(f"Invalid threshold_usd: {THRESHOLD_USD!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with movements as (
    select "to" as holder, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}' and contract_address = from_hex('{contract_hex}')
    union all
    select "from" as holder, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}' and contract_address = from_hex('{contract_hex}')
),
balances as (
    select holder, sum(amt) as balance
    from movements
    group by holder
    having sum(amt) > 0
)
select
    count(*) as holder_count,
    count(*) filter (where balance >= {THRESHOLD_USD}) as whale_count,
    {THRESHOLD_USD} as threshold_usd
from balances
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
