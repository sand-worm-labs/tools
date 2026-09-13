# Sandworm Power Toolbox — {{__tool_name}}
import re

TOKEN_SYMBOL = "{{token_symbol}}".strip()
START_DT = "{{start_dt}}"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

if not TOKEN_SYMBOL:
    raise ValueError("token_symbol is required")
if not DATE_RE.match(START_DT):
    raise ValueError(f"Invalid start_dt: {START_DT!r}")

# IL for a 50/50 pool of TOKEN_SYMBOL against a stable, relative to just holding
# the token: IL = 2*sqrt(r)/(1+r) - 1, where r is the price ratio vs start_dt.
sql = f"""
with daily as (
    select date_trunc('day', minute) as dt, avg(price) as price
    from prices.usd
    where upper(symbol) = upper('{TOKEN_SYMBOL}')
      and minute >= date('{START_DT}')
    group by 1
),
base as (
    select price as start_price
    from daily
    order by dt
    limit 1
)
select
    d.dt,
    d.price,
    (2 * sqrt(d.price / nullif(b.start_price, 0)) / (1 + d.price / nullif(b.start_price, 0)) - 1) * 100 as il_percentage
from daily d
cross join base b
order by d.dt
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="dt", y=['il_percentage'])
fig.show()

{{__df_name}}
