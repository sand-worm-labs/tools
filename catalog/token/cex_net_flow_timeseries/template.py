# Sandworm Power Toolbox — {{__tool_name}}
# Unlike cex_net_flow_daily (which takes an explicit CEX address list), this
# tool auto-discovers CEX wallets via labels.addresses for a broad trend view.
import re
from datetime import datetime

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
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

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with cex_wallets as (
    select address
    from labels.addresses
    where blockchain = '{CHAIN}'
      and category = 'cex'
),
inflow as (
    select date_trunc('day', t.block_time) as day, sum(t.amount) as amt
    from tokens.transfers t
    join cex_wallets c on c.address = t."to"
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.contract_address = from_hex('{contract_hex}')
      and t.block_time >= date '{DATE_FROM}'
    group by day
),
outflow as (
    select date_trunc('day', t.block_time) as day, sum(t.amount) as amt
    from tokens.transfers t
    join cex_wallets c on c.address = t."from"
    where t.blockchain = '{CHAIN}'
      and t.token_standard = 'erc20'
      and t.contract_address = from_hex('{contract_hex}')
      and t.block_time >= date '{DATE_FROM}'
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
