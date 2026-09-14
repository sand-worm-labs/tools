# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()
TOP_N = "{{top_n}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")
if TOP_N and not (TOP_N.isdigit() and int(TOP_N) > 0):
    raise ValueError(f"Invalid top_n: {TOP_N!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
limit_clause = f"limit {TOP_N}" if TOP_N else ""

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
),
net as (
    select
        coalesce(i.wallet, o.wallet) as wallet,
        coalesce(i.inflow_amt, 0) - coalesce(o.outflow_amt, 0) as net_inflow
    from inflow i
    full outer join outflow o on i.wallet = o.wallet
)
select
    to_hex(wallet) as wallet,
    net_inflow,
    row_number() over (order by net_inflow desc) as rank
from net
order by net_inflow desc
{limit_clause}
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
