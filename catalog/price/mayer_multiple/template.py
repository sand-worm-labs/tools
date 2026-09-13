# Sandworm Power Toolbox — {{__tool_name}}
TOKEN_SYMBOL = "{{token_symbol}}".strip()
MA_SHORT = "{{ma_short}}".strip() or "30"
MA_LONG = "{{ma_long}}".strip() or "200"

if not TOKEN_SYMBOL:
    raise ValueError("token_symbol is required")
if not (MA_SHORT.isdigit() and int(MA_SHORT) > 0):
    raise ValueError(f"Invalid ma_short: {MA_SHORT!r}")
if not (MA_LONG.isdigit() and int(MA_LONG) > 0):
    raise ValueError(f"Invalid ma_long: {MA_LONG!r}")

lookback_days = int(MA_LONG) * 2

sql = f"""
with daily as (
    select date_trunc('day', minute) as day, avg(price) as price
    from prices.usd
    where upper(symbol) = upper('{TOKEN_SYMBOL}')
      and minute >= now() - interval '{lookback_days}' day
    group by 1
)
select
    day,
    price,
    avg(price) over (order by day rows between {int(MA_SHORT) - 1} preceding and current row) as ma_short,
    avg(price) over (order by day rows between {int(MA_LONG) - 1} preceding and current row) as ma_long,
    price / nullif(avg(price) over (order by day rows between {int(MA_LONG) - 1} preceding and current row), 0) as multiple
from daily
order by day
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="day", y=['price', 'ma_short', 'ma_long'])
fig.show()

{{__df_name}}
