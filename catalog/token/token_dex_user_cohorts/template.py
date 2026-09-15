# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
INTERVAL = "{{interval}}".strip() or "week"

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

sql = f"""
with trades as (
    select taker, block_time
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{token_hex}') or token_sold_address = from_hex('{token_hex}'))
),
first_trade as (
    select taker, min(block_time) as first_time
    from trades
    group by taker
),
activity as (
    select
        date_trunc('{INTERVAL}', t.block_time) as time,
        t.taker,
        date_trunc('{INTERVAL}', f.first_time) as first_period
    from trades t
    join first_trade f on f.taker = t.taker
)
select
    time,
    count(distinct taker) filter (where first_period = time) as new,
    count(distinct taker) filter (where first_period < time) as returning
from activity
group by time
order by time
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
