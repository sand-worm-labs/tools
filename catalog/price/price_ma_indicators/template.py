# Sandworm Power Toolbox — {{__tool_name}}
TOKEN_SYMBOL = "{{token_symbol}}".strip()
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "50"

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
)
select
    day,
    price,
    lag(price) over (order by day) as prev_price,
    avg(price) over (order by day rows between 6 preceding and current row) as ma7,
    avg(price) over (order by day rows between 19 preceding and current row) as ma20,
    avg(price) over (order by day rows between 49 preceding and current row) as ma50
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="day", y=['price', 'ma7', 'ma20', 'ma50'])
fig.show()

{{__df_name}}
