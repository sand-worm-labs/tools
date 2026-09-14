# Sandworm Power Toolbox — {{__tool_name}}

CHAIN = "{{chain}}"
LOOKBACK_DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

# Cross-token screener: ranks every symbol priced on this chain (via
# prices.usd) rather than a single token, matching the "Multi-token price
# stats" scope described in tool.yaml.
sql = f"""
with px as (
    select symbol, date_trunc('day', minute) as day, avg(price) as price
    from prices.usd
    where blockchain = '{CHAIN}'
      and minute >= now() - interval '{LOOKBACK_DAYS}' day
      and symbol is not null
    group by 1, 2
),
rets as (
    select
        symbol,
        day,
        price / nullif(lag(price) over (partition by symbol order by day), 0) - 1 as ret
    from px
),
stats as (
    select
        symbol,
        avg(ret) * 365 as ann_return,
        stddev_samp(ret) * sqrt(365) as ann_stdev,
        stddev_samp(case when ret < 0 then ret end) * sqrt(365) as downside_stdev
    from rets
    where ret is not null
    group by symbol
),
running_peak as (
    select
        symbol,
        day,
        price,
        max(price) over (partition by symbol order by day rows between unbounded preceding and current row) as peak
    from px
),
drawdown as (
    select symbol, min(price / nullif(peak, 0) - 1) as max_drawdown
    from running_peak
    group by symbol
)
select
    s.symbol as token,
    s.ann_return / nullif(s.ann_stdev, 0) as sharpe,
    s.ann_return / nullif(s.downside_stdev, 0) as sortino,
    s.ann_return / nullif(abs(d.max_drawdown), 0) as calmar,
    s.ann_stdev as stdev
from stats s
join drawdown d on d.symbol = s.symbol
where s.ann_stdev is not null
order by sharpe desc
limit 50
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
