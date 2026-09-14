# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}"
MIN_USD = "{{min_usd}}".strip() or "0"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")
if not MIN_USD.replace(".", "", 1).isdigit():
    raise ValueError(f"Invalid min_usd: {MIN_USD!r}")

sql = f"""
with trades as (
    select token_bought_symbol as token_symbol, taker, amount_usd, block_time
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
      and amount_usd >= {MIN_USD}
      and token_bought_symbol is not null
)
select
    token_symbol,
    count(distinct taker) as unique_traders,
    count(*) as total_trades,
    sum(amount_usd) as total_volume,
    min(block_time) as first_trade,
    max(block_time) as last_trade,
    avg(amount_usd) as avg_trade_size
from trades
group by token_symbol
order by total_volume desc
limit 200
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
