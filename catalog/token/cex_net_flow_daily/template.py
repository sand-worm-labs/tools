# Sandworm Power Toolbox — {{__tool_name}}
import re
from datetime import datetime

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
CEX_ADDRESSES_RAW = '''{{cex_addresses}}'''.replace("[", "").replace("]", "").replace('"', "")
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")

cex_addresses = [a.strip() for a in CEX_ADDRESSES_RAW.split(",") if a.strip()]
if not cex_addresses:
    raise ValueError("At least one cex_addresses entry is required")
for a in cex_addresses:
    if not ADDRESS_RE.match(a):
        raise ValueError(f"Invalid cex_addresses entry: {a!r}")

if DATE_FROM:
    try:
        datetime.strptime(DATE_FROM, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
cex_hex_list = ", ".join(f"from_hex('{a[2:].lower()}')" for a in cex_addresses)
date_filter = f"and block_time >= date '{DATE_FROM}'" if DATE_FROM else ""

sql = f"""
with inflow as (
    select date_trunc('day', block_time) as day, sum(amount) as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and "to" in ({cex_hex_list})
      {date_filter}
    group by day
),
outflow as (
    select date_trunc('day', block_time) as day, sum(amount) as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{contract_hex}')
      and "from" in ({cex_hex_list})
      {date_filter}
    group by day
)
select
    cast(coalesce(i.day, o.day) as date) as day,
    coalesce(i.amt, 0) - coalesce(o.amt, 0) as net_flow,
    coalesce(i.amt, 0) as inflow,
    coalesce(o.amt, 0) as outflow
from inflow i
full outer join outflow o on i.day = o.day
order by day
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
