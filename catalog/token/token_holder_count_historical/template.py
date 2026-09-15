# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
INTERVAL = "{{interval}}".strip() or "day"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_INTERVALS = {"minute", "hour", "day", "week", "month"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if INTERVAL not in ALLOWED_INTERVALS:
    raise ValueError(f"Unsupported interval: {INTERVAL!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()
zero_hex = "0" * 40

sql = f"""
with movements as (
    select date_trunc('{INTERVAL}', block_time) as period, "to" as address, amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "to" <> from_hex('{zero_hex}')
    union all
    select date_trunc('{INTERVAL}', block_time) as period, "from" as address, -amount as amt
    from tokens.transfers
    where blockchain = '{CHAIN}'
      and token_standard = 'erc20'
      and contract_address = from_hex('{token_hex}')
      and "from" <> from_hex('{zero_hex}')
),
period_net as (
    select period, address, sum(amt) as net_change
    from movements
    group by period, address
),
running as (
    select
        period,
        address,
        sum(net_change) over (partition by address order by period) as balance
    from period_net
)
select
    period as date,
    count(*) filter (where balance > 0) as holder_count
from running
group by period
order by period
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
