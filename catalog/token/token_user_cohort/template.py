# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
INTERVAL = "{{interval}}"

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
    select taker as trader, date_trunc('{INTERVAL}', block_time) as period
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{contract_hex}') or token_sold_address = from_hex('{contract_hex}'))
),
first_seen as (
    select trader, min(period) as first_period
    from trades
    group by trader
),
activity as (
    select distinct trader, period from trades
)
select
    a.period as time,
    count(distinct case when a.period = f.first_period then a.trader end) as new_users,
    count(distinct case when a.period > f.first_period then a.trader end) as returning_users
from activity a
join first_seen f on f.trader = a.trader
group by a.period
order by a.period
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
