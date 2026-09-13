# Sandworm Power Toolbox — {{__tool_name}}
TOKEN_SYMBOL = "{{token_symbol}}".strip()
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "90"

if not TOKEN_SYMBOL:
    raise ValueError("token_symbol is required")
if not (LOOKBACK_DAYS.isdigit() and int(LOOKBACK_DAYS) > 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

sql = f"""
with daily as (
    select date_trunc('day', minute) as day, avg(price) as close
    from prices.usd
    where upper(symbol) = upper('{TOKEN_SYMBOL}')
      and minute >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1
),
bands as (
    select
        day,
        close,
        avg(close) over (order by day rows between 29 preceding and current row) as sma30,
        stddev(close) over (order by day rows between 29 preceding and current row) as sd30
    from daily
)
select
    day,
    close,
    sma30,
    sma30 + 2 * sd30 as upper_band,
    sma30 - 2 * sd30 as lower_band
from bands
order by day
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="day", y=['close', 'sma30', 'upper_band', 'lower_band'])
fig.show()

{{__df_name}}
