# Sandworm Power Toolbox — {{__tool_name}}
import json


def _parse_date_range(raw):
    raw = raw.strip()
    if not raw:
        return None, None
    try:
        d = json.loads(raw)
        return d.get("from") or None, d.get("to") or None
    except (json.JSONDecodeError, AttributeError, TypeError):
        return None, None


PORTFOLIO_SYMBOL = "{{portfolio_symbol}}".strip()
TOKEN_SYMBOL = "{{token_symbol}}".strip()
DATE_FROM, DATE_TO = _parse_date_range("""{{date_range}}""")

if not PORTFOLIO_SYMBOL:
    raise ValueError("portfolio_symbol is required")
if not TOKEN_SYMBOL:
    raise ValueError("token_symbol is required")

date_from_clause = f"and port.day >= date('{DATE_FROM}')" if DATE_FROM else "and port.day >= now() - interval '180' day"
date_to_clause = f"and port.day <= date('{DATE_TO}')" if DATE_TO else ""

sql = f"""
with port as (
    select date_trunc('day', minute) as day, avg(price) as price
    from prices.usd where upper(symbol) = upper('{PORTFOLIO_SYMBOL}') group by 1
),
mkt as (
    select date_trunc('day', minute) as day, avg(price) as price
    from prices.usd where upper(symbol) = upper('{TOKEN_SYMBOL}') group by 1
),
joined as (
    select port.day, port.price as port_price, mkt.price as mkt_price
    from port join mkt on port.day = mkt.day
    where 1 = 1 {date_from_clause} {date_to_clause}
),
returns as (
    select
        day,
        (port_price - lag(port_price) over (order by day)) / nullif(lag(port_price) over (order by day), 0) as port_ret,
        (mkt_price - lag(mkt_price) over (order by day)) / nullif(lag(mkt_price) over (order by day), 0) as mkt_ret
    from joined
)
select
    day,
    covar_samp(port_ret, mkt_ret) over (order by day rows between 29 preceding and current row)
        / nullif(var_samp(mkt_ret) over (order by day rows between 29 preceding and current row), 0) as beta,
    port_ret,
    mkt_ret
from returns
order by day
"""

{{__df_name}} = _sandworm_query(sql)

import plotly.express as px

fig = px.line({{__df_name}}, x="day", y=['beta'])
fig.show()

{{__df_name}}
