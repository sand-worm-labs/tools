# Sandworm Power Toolbox — {{__tool_name}}
import re

CONTRACT_ADDRESS = "{{contract_address}}"
CHAIN = "{{chain}}"
DATE_FROM = "{{date_from}}".strip()
MIN_USD = "{{min_usd}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if DATE_FROM and not DATE_RE.match(DATE_FROM):
    raise ValueError(f"Invalid date_from: {DATE_FROM!r}")
try:
    min_usd_val = float(MIN_USD) if MIN_USD else 5000.0
except ValueError:
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")

contract_hex = CONTRACT_ADDRESS[2:].lower()
date_where = f"and block_time >= date('{DATE_FROM}')" if DATE_FROM else ""

sql = f"""
with trades as (
    select
        taker,
        case when token_bought_address = from_hex('{contract_hex}') then token_bought_amount_usd else 0 end as buy_usd,
        case when token_sold_address = from_hex('{contract_hex}') then token_sold_amount_usd else 0 end as sell_usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{contract_hex}') or token_sold_address = from_hex('{contract_hex}'))
      and amount_usd >= {min_usd_val}
      {date_where}
),
net as (
    select taker, sum(buy_usd) - sum(sell_usd) as net_usd
    from trades
    group by taker
),
tiered as (
    select
        taker,
        net_usd,
        case
            when net_usd < 0 then 'net_seller'
            when net_usd < 1000 then 'micro (<$1k)'
            when net_usd < 10000 then 'small ($1k-$10k)'
            when net_usd < 100000 then 'medium ($10k-$100k)'
            when net_usd < 1000000 then 'large ($100k-$1M)'
            else 'whale (>=$1M)'
        end as tier
    from net
)
select
    tier,
    count(*) as wallet_count,
    min(net_usd) as min_balance,
    max(net_usd) as max_balance
from tiered
group by tier
order by min(net_usd)
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
