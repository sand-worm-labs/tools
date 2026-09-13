# Sandworm Power Toolbox — {{__tool_name}}
LOOKBACK_DAYS = "{{lookback_days}}".strip()

if LOOKBACK_DAYS and not (LOOKBACK_DAYS.isdigit() and int(LOOKBACK_DAYS) > 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

window_days = LOOKBACK_DAYS or "1460"

sql = f"""
with halvings as (
    select * from (values
        (date('2012-11-28')),
        (date('2016-07-09')),
        (date('2020-05-11')),
        (date('2024-04-20'))
    ) as t(halving_date)
),
daily as (
    select date_trunc('day', minute) as day, avg(price) as price
    from prices.usd
    where upper(symbol) = 'BTC'
    group by 1
),
post_halving as (
    select
        h.halving_date,
        d.day,
        d.price,
        date_diff('day', h.halving_date, d.day) as days_since,
        max(d.price) over (partition by h.halving_date order by d.day) as running_peak
    from halvings h
    join daily d
        on d.day >= h.halving_date
       and d.day <= h.halving_date + interval '{window_days}' day
),
drawdowns as (
    select
        halving_date,
        days_since,
        (price - running_peak) / nullif(running_peak, 0) * 100 as drawdown_pct
    from post_halving
)
select halving_date, drawdown_pct, days_since
from drawdowns
where (halving_date, drawdown_pct) in (
    select halving_date, min(drawdown_pct) from drawdowns group by halving_date
)
order by halving_date
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.bar({{__df_name}}, x="halving_date", y="drawdown_pct")
fig.show()

{{__df_name}}
