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

contract_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with buys as (
    select taker as buyer, block_time
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_address = from_hex('{contract_hex}')
),
first_buy as (
    select buyer, min(block_time) as first_time
    from buys
    group by buyer
),
tagged as (
    select distinct
        b.buyer,
        date_trunc('{INTERVAL}', b.block_time) as period,
        date_trunc('{INTERVAL}', f.first_time) as first_period
    from buys b
    join first_buy f on f.buyer = b.buyer
)
select
    cast(period as varchar) as period,
    count(distinct case when period = first_period then buyer end) as new_buyers,
    count(distinct case when period <> first_period then buyer end) as repeat_buyers,
    100.0 * count(distinct case when period <> first_period then buyer end)
        / nullif(count(distinct buyer), 0) as repeat_pct
from tagged
group by period
order by period
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
