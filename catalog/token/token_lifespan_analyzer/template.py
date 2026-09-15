# Sandworm Power Toolbox — {{__tool_name}}
CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "30"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

sql = f"""
with trades as (
    select blockchain, token_bought_address as token_address, block_time
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
    union all
    select blockchain, token_sold_address as token_address, block_time
    from dex.trades
    where blockchain = '{CHAIN}'
      and block_time >= now() - interval '{LOOKBACK_DAYS}' day
),
per_token as (
    select
        blockchain,
        token_address,
        count(*) as trades,
        min(block_time) as first_trade,
        max(block_time) as last_trade
    from trades
    group by blockchain, token_address
),
bucketed as (
    select
        blockchain,
        trades,
        first_trade,
        last_trade,
        date_diff('day', first_trade, last_trade) as lifespan_days
    from per_token
)
select
    blockchain,
    case
        when lifespan_days < 1 then '<1 day'
        when lifespan_days < 7 then '1-7 days'
        when lifespan_days < 30 then '7-30 days'
        else '30+ days'
    end as lifespan_bucket,
    sum(trades) as trades,
    cast(min(first_trade) as date) as first_trade,
    cast(max(last_trade) as date) as last_trade
from bucketed
group by blockchain, lifespan_bucket
order by lifespan_bucket
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
