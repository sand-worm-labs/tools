# Sandworm Power Toolbox — {{__tool_name}}
import re

TOKEN_SYMBOL = "{{token_symbol}}".strip()
CHAIN = "{{chain}}"
TIMERANGE = "{{timerange}}".strip()

ALLOWED_CHAINS = {"ethereum", "base", "optimism", "arbitrum", "polygon", "bsc", "avalanche", "celo"}
RANGE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}),(\d{4}-\d{2}-\d{2})$")

if not TOKEN_SYMBOL:
    raise ValueError("token_symbol is required")
if CHAIN not in ALLOWED_CHAINS:
    raise ValueError(f"Unsupported chain: {CHAIN!r}")

m = RANGE_RE.match(TIMERANGE) if TIMERANGE else None
if TIMERANGE and not m:
    raise ValueError(f"Invalid timerange, expected 'YYYY-MM-DD,YYYY-MM-DD': {TIMERANGE!r}")

date_clause = (
    f"and minute between date('{m.group(1)}') and date('{m.group(2)}')"
    if m else "and minute >= now() - interval '730' day"
)

sql = f"""
with daily as (
    select date_trunc('day', minute) as day, avg(price) as price
    from prices.usd
    where upper(symbol) = upper('{TOKEN_SYMBOL}')
      and blockchain = '{CHAIN}'
      {date_clause}
    group by 1
),
ranked as (
    select day, price, row_number() over (partition by year(day), month(day) order by day desc) as rn
    from daily
),
monthly as (
    select year(day) as year, month(day) as month, price as month_end_price
    from ranked
    where rn = 1
),
monthly_returns as (
    select
        year, month,
        (month_end_price - lag(month_end_price) over (order by year, month))
            / nullif(lag(month_end_price) over (order by year, month), 0) as ret
    from monthly
)
select
    year,
    month,
    (avg(ret) over ()) / nullif(stddev(ret) over (), 0) * sqrt(12) as sharpe,
    (avg(ret) over ()) / nullif(stddev(case when ret < 0 then ret end) over (), 0) * sqrt(12) as sortino
from monthly_returns
where ret is not null
order by year, month
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="month", y=["sharpe", "sortino"], color=None)
fig.show()

{{__df_name}}
