# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with inflow as (
    select "to" as wallet, sum(amount) as inflow_amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{contract_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
),
outflow as (
    select "from" as wallet, sum(amount) as outflow_amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{contract_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
)
select
    to_hex(coalesce(i.wallet, o.wallet)) as wallet,
    coalesce(i.inflow_amt, 0) - coalesce(o.outflow_amt, 0) as net,
    coalesce(i.inflow_amt, 0) as inflows,
    coalesce(o.outflow_amt, 0) as outflows
from inflow i
full outer join outflow o on i.wallet = o.wallet
order by net desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
