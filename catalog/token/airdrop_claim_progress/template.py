# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
DISTRIBUTOR_ADDRESS = "{{distributor_address}}"
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not ADDRESS_RE.match(DISTRIBUTOR_ADDRESS):
    raise ValueError(f"Invalid distributor_address: {DISTRIBUTOR_ADDRESS!r}")
if DATE_FROM and not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
distributor_hex = DISTRIBUTOR_ADDRESS[2:].lower()
date_where = f"and block_time >= date '{DATE_FROM}'" if DATE_FROM else ""

# pct_claimed is expressed against the token's total_supply (no separate
# "total eligible" input is defined for this tool).
sql = f"""
with claims as (
    select block_time, "to" as claimer, amount
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{contract_hex}')
      and "from" = from_hex('{distributor_hex}')
      {date_where}
),
daily as (
    select
        date_trunc('day', block_time) as day,
        count(distinct claimer) as unique_claimers,
        sum(amount) as claimed
    from claims
    group by 1
),
supply as (
    select total_supply / power(10, coalesce(decimals, 18)) as total_supply
    from tokens.erc20
    where blockchain = '{CHAIN}' and contract_address = from_hex('{contract_hex}')
)
select
    d.day as date,
    d.unique_claimers,
    sum(d.claimed) over (order by d.day) as total_claimed,
    100.0 * sum(d.claimed) over (order by d.day) / nullif((select total_supply from supply), 0) as pct_claimed
from daily d
order by d.day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
