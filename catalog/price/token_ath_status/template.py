# Sandworm Power Toolbox — {{__tool_name}}
LOOKBACK_DAYS = "{{lookback_days}}".strip() or "30"

if not (LOOKBACK_DAYS.isdigit() and int(LOOKBACK_DAYS) > 0):
    raise ValueError(f"Invalid lookback_days: {LOOKBACK_DAYS!r}")

# No token filter exists on this tool, so it scans the full prices.usd universe
# over the lookback window.
sql = f"""
with daily as (
    select date_trunc('day', minute) as date, symbol, avg(price) as price
    from prices.usd
    where minute >= now() - interval '{LOOKBACK_DAYS}' day
    group by 1, 2
),
with_ath as (
    select
        symbol, date, price,
        max(price) over (partition by symbol order by date) as ath
    from daily
)
select
    symbol, date, price, ath,
    case when price >= ath then 'new_ath' else 'below_ath' end as status
from with_ath
order by symbol, date
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="date", y=['price', 'ath'])
fig.show()

{{__df_name}}
