# Sandworm Power Toolbox — {{__tool_name}}

CHAIN = "{{chain}}"
TOKEN_SYMBOL = "{{token_symbol}}".strip().upper()
LOOKBACK_DAYS = "{{lookback_days}}"

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}

if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")
if not TOKEN_SYMBOL:
    raise ValueError("token_symbol is required")
if not LOOKBACK_DAYS.isdigit() or int(LOOKBACK_DAYS) <= 0:
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

symbol_sql = TOKEN_SYMBOL.replace("'", "''")

sql = f"""
with px as (
    select date_trunc('day', minute) as day, avg(price) as price
    from prices.usd
    where blockchain = '{CHAIN}'
      and symbol = '{symbol_sql}'
      and minute >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
),
rets as (
    select day, price / nullif(lag(price) over (order by day), 0) - 1 as ret
    from px
),
stats as (
    select
        avg(ret) * 365 as ann_return,
        stddev_samp(ret) * sqrt(365) as ann_stdev,
        stddev_samp(case when ret < 0 then ret end) * sqrt(365) as downside_stdev
    from rets
    where ret is not null
),
running_peak as (
    select day, price, max(price) over (order by day rows between unbounded preceding and current row) as peak
    from px
),
drawdown as (
    select min(price / nullif(peak, 0) - 1) as max_drawdown from running_peak
)
select
    '{symbol_sql}' as token,
    s.ann_return / nullif(s.ann_stdev, 0) as sharpe,
    s.ann_return / nullif(s.downside_stdev, 0) as sortino,
    s.ann_return / nullif(abs(d.max_drawdown), 0) as calmar,
    s.ann_return as ann_return,
    s.ann_stdev as ann_stdev
from stats s
cross join drawdown d
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
