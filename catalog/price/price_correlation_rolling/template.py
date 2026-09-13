# Sandworm Power Toolbox — {{__tool_name}}
TOKEN1 = "{{token1}}".strip()
TOKEN2 = "{{token2}}".strip()
WINDOW = "{{window}}".strip() or "30"

if not TOKEN1:
    raise ValueError("token1 is required")
if not TOKEN2:
    raise ValueError("token2 is required")
if not (WINDOW.isdigit() and int(WINDOW) > 0):
    raise ValueError(f"Invalid window: {WINDOW!r}")

sql = f"""
with p1 as (
    select date_trunc('day', minute) as day, avg(price) as price
    from prices.usd where upper(symbol) = upper('{TOKEN1}') group by 1
),
p2 as (
    select date_trunc('day', minute) as day, avg(price) as price
    from prices.usd where upper(symbol) = upper('{TOKEN2}') group by 1
),
joined as (
    select p1.day, p1.price as price1, p2.price as price2
    from p1 join p2 on p1.day = p2.day
),
returns as (
    select
        day,
        (price1 - lag(price1) over (order by day)) / nullif(lag(price1) over (order by day), 0) as r1,
        (price2 - lag(price2) over (order by day)) / nullif(lag(price2) over (order by day), 0) as r2
    from joined
)
select
    day as date,
    corr(r1, r2) over (order by day rows between {int(WINDOW) - 1} preceding and current row) as corr
from returns
order by day
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="date", y=['corr'])
fig.show()

{{__df_name}}
