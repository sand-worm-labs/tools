# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip()
MIN_TRADES = "{{min_trades}}".strip() or "10"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")
if not MIN_TRADES.isdigit() or int(MIN_TRADES) < 0:
    raise ValueError(f"Invalid min_trades: {MIN_TRADES!r}")

sql = f"""
with trades as (
    select token_bought_symbol, token_sold_symbol, taker
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
buyers as (
    select token_bought_symbol as token_symbol, count(distinct taker) as buyers
    from trades
    group by 1
),
sellers as (
    select token_sold_symbol as token_symbol, count(distinct taker) as sellers
    from trades
    group by 1
)
select
    coalesce(b.token_symbol, s.token_symbol) as token_symbol,
    coalesce(b.buyers, 0) as buyers,
    coalesce(s.sellers, 0) as sellers,
    cast(coalesce(b.buyers, 0) as double) / nullif(coalesce(s.sellers, 0), 0) as ratio
from buyers b
full outer join sellers s on s.token_symbol = b.token_symbol
where coalesce(b.buyers, 0) + coalesce(s.sellers, 0) >= {MIN_TRADES}
order by ratio desc nulls last
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
