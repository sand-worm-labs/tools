# Sandworm Power Toolbox — {{__tool_name}}
# No perpetuals/margin "long/short" concept exists for a spot DEX, so this is
# reinterpreted as directional spot pressure per trader: "long" = net buy
# volume (accumulating), "short" = net sell volume, in each hourly bucket.
import re

CHAIN = "{{chain}}"
CONTRACT_ADDRESS = "{{contract_address}}"
START_TIMESTAMP = "{{start_timestamp}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(CONTRACT_ADDRESS):
    raise ValueError(f"Invalid contract_address: {CONTRACT_ADDRESS!r}")
if not DATE_RE.match(START_TIMESTAMP):
    raise ValueError(f"Invalid start_timestamp: {START_TIMESTAMP!r}")

token_hex = CONTRACT_ADDRESS[2:].lower()

sql = f"""
with trades as (
    select
        date_trunc('hour', block_time) as hour,
        taker,
        case when token_bought_address = from_hex('{token_hex}') then amount_usd else 0 end as long_usd,
        case when token_sold_address = from_hex('{token_hex}') then amount_usd else 0 end as short_usd
    from dex.trades
    where blockchain = '{CHAIN}'
      and (token_bought_address = from_hex('{token_hex}') or token_sold_address = from_hex('{token_hex}'))
      and block_time >= date('{START_TIMESTAMP}')
)
select
    hour,
    to_hex(taker) as trader,
    sum(long_usd) - sum(short_usd) as net_position,
    sum(long_usd) / nullif(sum(short_usd), 0) as ratio
from trades
group by hour, taker
order by hour, net_position desc
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
