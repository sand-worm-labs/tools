# Sandworm Power Toolbox — {{__tool_name}}
TOKEN_SYMBOL = "{{token_symbol}}".strip()
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "365"

if not TOKEN_SYMBOL:
    raise ValueError("token_symbol is required")
if not (LOOKBACK_DAYS.isdigit() and int(LOOKBACK_DAYS) > 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

sql = f"""
with daily as (
    select date_trunc('day', minute) as day, avg(price) as price
    from prices.usd
    where upper(symbol) = upper('{TOKEN_SYMBOL}')
      and minute >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
),
returns as (
    select day, (price - lag(price) over (order by day)) / nullif(lag(price) over (order by day), 0) as r
    from daily
)
select
    max(day) as day,
    avg(r) as avg_return,
    stddev(r) as std_dev,
    skewness(r) as skewness,
    kurtosis(r) as kurtosis
from returns
where r is not null
"""

{{__df_name}} = _sandworm_query(sql)
{{__df_name}}
