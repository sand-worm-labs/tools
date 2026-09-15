# Sandworm Power Toolbox — {{__tool_name}}
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
INTERVAL = "{{interval}}".strip() or "day"
DATE_FROM = "{{date_from}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ALLOWED_INTERVALS = {"minute", "hour", "day", "week", "month"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if INTERVAL not in ALLOWED_INTERVALS:
    raise ValueError(f"Unsupported interval: {INTERVAL!r}")
if not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with period_prices as (
    select date_trunc('{INTERVAL}', minute) as dt, avg(price) as period_price
    from prices.usd
    where blockchain = '{CHAIN}'
      and contract_address = from_hex('{token_hex}')
      and minute >= date('{DATE_FROM}')
    group by 1
),
cum_avg as (
    select
        dt,
        period_price,
        avg(period_price) over (order by dt rows between unbounded preceding and current row) as avg_price
    from period_prices
),
latest as (
    select period_price as current_price
    from period_prices
    order by dt desc
    limit 1
)
select
    c.dt,
    c.avg_price,
    l.current_price,
    (l.current_price / nullif(c.avg_price, 0)) - 1 as dca_return
from cum_avg c
cross join latest l
order by c.dt
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
