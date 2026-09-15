# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
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

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with trades as (
    select
        taker,
        date_trunc('{INTERVAL}', block_time) as period
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{contract_hex}') or token_sold_address = from_hex('{contract_hex}'))
),
first_trade as (
    select taker, min(period) as first_period
    from trades
    group by taker
),
activity as (
    select distinct taker, period
    from trades
)
select
    a.period as time,
    count(*) filter (where a.period = f.first_period) as new,
    count(*) filter (where a.period > f.first_period) as returning
from activity a
join first_trade f on f.taker = a.taker
group by a.period
order by a.period
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
