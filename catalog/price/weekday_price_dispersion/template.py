# Sandworm Power Toolbox — {{__tool_name}}
TOKEN_SYMBOL = "{{token_symbol}}".strip()
NUMBER_OF_DAYS = "{{number_of_days}}".strip()

if not TOKEN_SYMBOL:
    raise ValueError("token_symbol is required")
if not (NUMBER_OF_DAYS.isdigit() and int(NUMBER_OF_DAYS) > 0):
    raise ValueError(f"Invalid number_of_days: {NUMBER_OF_DAYS!r}")

sql = f"""
with intraday as (
    select
        date_trunc('day', minute) as day,
        day_of_week(minute) as weekday,
        min(price) as day_min,
        max(price) as day_max,
        min_by(price, minute) as open_price
    from prices.usd
    where upper(symbol) = upper('{TOKEN_SYMBOL}')
      and minute >= now() - interval '{NUMBER_OF_DAYS}' day
    group by 1, 2
)
select
    weekday,
    min(day_min) as min_px,
    max(day_max) as max_px,
    avg((day_max - day_min) / nullif(open_price, 0) * 100) as dispersion_pct
from intraday
group by weekday
order by weekday
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="weekday", y="dispersion_pct")
fig.show()

{{__df_name}}
