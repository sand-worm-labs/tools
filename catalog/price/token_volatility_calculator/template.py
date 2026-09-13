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
    select day, ln(price / nullif(lag(price) over (order by day), 0)) as log_ret
    from daily
)
select
    day,
    stddev(log_ret) over (order by day rows between 29 preceding and current row) * sqrt(365) as volatility_30d,
    stddev(log_ret) over (order by day rows between 89 preceding and current row) * sqrt(365) as volatility_90d,
    stddev(log_ret) over (order by day rows between 199 preceding and current row) * sqrt(365) as volatility_200d
from returns
order by day
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="day", y=['volatility_30d', 'volatility_90d', 'volatility_200d'])
fig.show()

{{__df_name}}
