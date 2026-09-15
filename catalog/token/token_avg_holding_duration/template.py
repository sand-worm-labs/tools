# Sandworm Power Toolbox — {{__tool_name}}
import re

TOKEN_MINT = "{{token_mint}}"
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "365"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not ADDRESS_RE.match(TOKEN_MINT):
    raise ValueError(f"Invalid token_mint: {TOKEN_MINT!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

token_hex = TOKEN_MINT[2:].lower()

sql = f"""
with buys as (
    select taker, min(block_time) as first_buy
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_bought_address = from_hex('{token_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    group by taker
),
sells as (
    select taker, block_time as sell_time
    from dex.trades
    where blockchain = '{CHAIN}'
      and token_sold_address = from_hex('{token_hex}')
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
round_trips as (
    select b.taker, b.first_buy, min(s.sell_time) as first_sell
    from buys b
    join sells s on s.taker = b.taker and s.sell_time > b.first_buy
    group by b.taker, b.first_buy
)
select
    avg(date_diff('hour', first_buy, first_sell)) as avg_duration,
    count(*) as trader_count
from round_trips
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
